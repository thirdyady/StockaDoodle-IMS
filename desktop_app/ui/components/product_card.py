from __future__ import annotations

import base64
import threading
from typing import Dict, Any, Callable, Optional, Tuple

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QObject, pyqtSignal, QRunnable, QThreadPool, QSize, QByteArray, QBuffer, QIODevice, QTimer
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QImage, QImageReader, QPainter, QPainterPath
)

from desktop_app.utils.helpers import get_feather_icon
from desktop_app.api_client.stockadoodle_api import StockaDoodleAPI


# -----------------------------
# GLOBAL: throttle concurrency
# -----------------------------
_MAX_INFLIGHT = 4
_image_sema = threading.Semaphore(_MAX_INFLIGHT)


# ✅ central card sizing (so grid can't stretch a single card to full row)
CARD_MIN_W = 280
CARD_MAX_W = 360

# ✅ thumbnail look tuning (contain, no crop)
THUMB_H = 130
THUMB_MIN_W = 160
THUMB_INNER_PAD = 6  # smaller = image appears larger inside container


class ThumbLabel(QLabel):
    """
    QLabel that DOES NOT let pixmap size affect layout sizing.
    This prevents the "growing card" sizeHint feedback loop.
    """
    def __init__(self, fixed_h: int = THUMB_H, min_w: int = THUMB_MIN_W, parent: QWidget | None = None):
        super().__init__(parent)
        self._fixed_h = int(fixed_h)
        self._min_w = int(min_w)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ✅ Important:
        # - Horizontal: Preferred (not Expanding) so the grid doesn't treat it as "eat all width"
        # - Vertical: Fixed (stable)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.setMinimumHeight(self._fixed_h)
        self.setMaximumHeight(self._fixed_h)
        self.setMinimumWidth(self._min_w)

    def sizeHint(self) -> QSize:  # stable hint (ignores pixmap)
        return QSize(max(self._min_w, 200), self._fixed_h)

    def minimumSizeHint(self) -> QSize:
        return QSize(self._min_w, self._fixed_h)


def _to_bytes(data: Any) -> Optional[bytes]:
    if data is None:
        return None
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, str):
        try:
            return base64.b64decode(data, validate=False)
        except Exception:
            return None
    if isinstance(data, dict):
        for k in ("image_data", "data", "bytes", "content"):
            if k in data and isinstance(data[k], str):
                try:
                    return base64.b64decode(data[k], validate=False)
                except Exception:
                    return None
            if k in data and isinstance(data[k], (bytes, bytearray)):
                return bytes(data[k])
    return None


def _scaled_decode(image_bytes: bytes, max_side: int = 1600) -> Optional[QImage]:
    if not image_bytes:
        return None

    ba = QByteArray(image_bytes)
    buf = QBuffer(ba)
    if not buf.open(QIODevice.OpenModeFlag.ReadOnly):
        return None

    reader = QImageReader(buf)
    reader.setAutoTransform(True)

    orig = reader.size()
    if orig.isValid() and orig.width() > 0 and orig.height() > 0:
        ow, oh = orig.width(), orig.height()
        scale = 1.0
        if max(ow, oh) > max_side:
            scale = max_side / float(max(ow, oh))
        sw = max(1, int(ow * scale))
        sh = max(1, int(oh * scale))
        reader.setScaledSize(QSize(sw, sh))

    img = reader.read()
    if img.isNull():
        return None
    return img


def _auto_trim_whitespace(
    img: QImage,
    bg_threshold: int = 245,
    alpha_threshold: int = 12,
    step: int = 2,
    pad: int = 6,   # ✅ smaller pad = tighter crop around object, still no "cut off" of object itself
) -> QImage:
    if img.isNull():
        return img

    img = img.convertToFormat(QImage.Format.Format_ARGB32)

    w = img.width()
    h = img.height()
    if w <= 2 or h <= 2:
        return img

    left = w
    right = 0
    top = h
    bottom = 0

    for y in range(0, h, step):
        for x in range(0, w, step):
            c = img.pixelColor(x, y)
            a = c.alpha()
            r = c.red()
            g = c.green()
            b = c.blue()

            is_bg = (a <= alpha_threshold) or (r >= bg_threshold and g >= bg_threshold and b >= bg_threshold)
            if not is_bg:
                if x < left:
                    left = x
                if x > right:
                    right = x
                if y < top:
                    top = y
                if y > bottom:
                    bottom = y

    if right <= left or bottom <= top:
        return img

    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(w - 1, right + pad)
    bottom = min(h - 1, bottom + pad)

    cw = max(1, right - left + 1)
    ch = max(1, bottom - top + 1)
    return img.copy(left, top, cw, ch)


def _contain_fit(img: QImage, target: QSize, inner_pad: int = THUMB_INNER_PAD) -> QImage:
    tw = max(1, target.width())
    th = max(1, target.height())

    canvas = QImage(tw, th, QImage.Format.Format_ARGB32_Premultiplied)
    canvas.fill(Qt.GlobalColor.transparent)

    if img.isNull():
        return canvas

    avail_w = max(1, tw - inner_pad * 2)
    avail_h = max(1, th - inner_pad * 2)

    fitted = img.scaled(
        avail_w,
        avail_h,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )

    x = (tw - fitted.width()) // 2
    y = (th - fitted.height()) // 2

    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    painter.drawImage(x, y, fitted)
    painter.end()

    return canvas


def _rounded_pixmap(pix: QPixmap, radius: int = 10) -> QPixmap:
    w = max(1, pix.width())
    h = max(1, pix.height())

    out = QPixmap(w, h)
    out.fill(Qt.GlobalColor.transparent)

    painter = QPainter(out)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    path = QPainterPath()
    path.addRoundedRect(0, 0, w, h, radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pix)
    painter.end()
    return out


class _WorkerSignals(QObject):
    finished = pyqtSignal(int, int, int, int, int, QImage)  # pid, gen, token, w, h, image
    error = pyqtSignal(int, int, int, int, int, str)        # pid, gen, token, w, h, msg


class _FetchThumbWorker(QRunnable):
    def __init__(self, api: StockaDoodleAPI, product_id: int, generation: int, token: int, target_size: QSize):
        super().__init__()
        self.api = api
        self.product_id = product_id
        self.generation = generation
        self.token = token
        self.target_size = target_size
        self.signals = _WorkerSignals()
        self.setAutoDelete(False)

    def run(self):
        _image_sema.acquire()
        try:
            raw = self.api.get_product_image(self.product_id)
            image_bytes = _to_bytes(raw)
            if not image_bytes:
                self.signals.error.emit(
                    self.product_id, self.generation, self.token,
                    self.target_size.width(), self.target_size.height(),
                    "no-bytes"
                )
                return

            img = _scaled_decode(image_bytes, max_side=1600)
            if img is None or img.isNull():
                self.signals.error.emit(
                    self.product_id, self.generation, self.token,
                    self.target_size.width(), self.target_size.height(),
                    "decode-failed"
                )
                return

            trimmed = _auto_trim_whitespace(img)
            thumb = _contain_fit(trimmed, self.target_size, inner_pad=THUMB_INNER_PAD)

            self.signals.finished.emit(
                self.product_id, self.generation, self.token,
                self.target_size.width(), self.target_size.height(),
                thumb
            )

        except Exception as e:
            self.signals.error.emit(
                self.product_id, self.generation, self.token,
                self.target_size.width(), self.target_size.height(),
                str(e)
            )
        finally:
            _image_sema.release()


class ProductCard(QFrame):
    _thumb_cache: dict[Tuple[int, int, int], QPixmap] = {}
    _thumb_gen: dict[int, int] = {}

    @classmethod
    def invalidate_thumb_cache(cls, product_id: Optional[int] = None) -> None:
        if product_id is None:
            cls._thumb_cache.clear()
            for pid in list(cls._thumb_gen.keys()):
                cls._thumb_gen[pid] = int(cls._thumb_gen.get(pid, 0)) + 1
            return

        pid = int(product_id)
        dead_keys = [k for k in cls._thumb_cache.keys() if k and k[0] == pid]
        for k in dead_keys:
            cls._thumb_cache.pop(k, None)
        cls._thumb_gen[pid] = int(cls._thumb_gen.get(pid, 0)) + 1

    @classmethod
    def _current_gen(cls, product_id: int) -> int:
        return int(cls._thumb_gen.get(int(product_id), 0))

    def __init__(
        self,
        product: Dict[str, Any],
        category_name: str = "—",
        on_edit: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_stock: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_delete: Optional[Callable[[Dict[str, Any]], None]] = None,
        api: Optional[StockaDoodleAPI] = None,
        parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.product = product
        self.category_name = category_name

        self.on_edit = on_edit
        self.on_stock = on_stock
        self.on_delete = on_delete

        self.api = api or StockaDoodleAPI()
        self.thread_pool = QThreadPool.globalInstance()

        self._active_workers: dict[Tuple[int, int, int, int], _FetchThumbWorker] = {}
        self._request_token: int = 0
        self._latest_token: int = 0

        self.setObjectName("productCard")

        # ✅ stop the grid from stretching the card to full width
        self.setMinimumWidth(CARD_MIN_W)
        self.setMaximumWidth(CARD_MAX_W)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self._built = False
        self._build()
        self._built = True

        QTimer.singleShot(0, self._ensure_thumb_loaded)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        name = str(self.product.get("name", ""))
        brand = str(self.product.get("brand", ""))
        price = float(self.product.get("price", 0) or 0)
        stock = int(self.product.get("stock_level", 0) or 0)
        min_stock = self.product.get("min_stock_level", "—")

        self.thumb = ThumbLabel(fixed_h=THUMB_H, min_w=THUMB_MIN_W)
        self.thumb.setObjectName("productThumb")
        root.addWidget(self.thumb)

        self._thumb_placeholder("Loading..." if self.product.get("has_image") else "No Image")

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        title = QLabel(name)
        title.setStyleSheet("font-size: 14px; font-weight: 800; color: #0F172A;")
        title_row.addWidget(title, 1)

        stock_badge = QLabel(f"Stock: {stock}")
        stock_badge.setObjectName("badge")
        stock_badge.setStyleSheet("""
            QLabel#badge {
                background: #EEF3FF;
                color: #0A2A83;
                padding: 2px 8px;
                border-radius: 999px;
                font-size: 10px;
                font-weight: 700;
            }
        """)
        title_row.addWidget(stock_badge, 0)
        root.addLayout(title_row)

        brand_lbl = QLabel(brand if brand else "—")
        brand_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: rgba(15,23,42,0.60);")

        cat_lbl = QLabel(self.category_name or "—")
        cat_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: rgba(15,23,42,0.60);")

        root.addWidget(brand_lbl)
        root.addWidget(cat_lbl)

        price_lbl = QLabel(f"₱{price:,.2f}")
        price_lbl.setStyleSheet("font-size: 18px; font-weight: 900; color: #0A2A83;")
        root.addWidget(price_lbl)

        actions = QHBoxLayout()
        actions.setSpacing(6)

        btn_edit = QPushButton()
        btn_stock = QPushButton()
        btn_delete = QPushButton()

        self._apply_icon(btn_edit, "edit-2", "Edit")
        self._apply_icon(btn_stock, "package", "Stock")
        self._apply_icon(btn_delete, "trash-2", "Delete")

        btn_edit.clicked.connect(lambda: self.on_edit(self.product) if self.on_edit else None)
        btn_stock.clicked.connect(lambda: self.on_stock(self.product) if self.on_stock else None)
        btn_delete.clicked.connect(lambda: self.on_delete(self.product) if self.on_delete else None)

        for b in (btn_edit, btn_stock, btn_delete):
            b.setFixedHeight(28)

        actions.addWidget(btn_edit)
        actions.addWidget(btn_stock)
        actions.addWidget(btn_delete)
        actions.addStretch()
        root.addLayout(actions)

        self.setToolTip(f"Min Stock: {min_stock}\nCategory: {self.category_name or '—'}")

        self.setStyleSheet("""
            QFrame#productCard {
                background: #FFFFFF;
                border: 1px solid #E2E8F5;
                border-radius: 14px;
            }
            QPushButton {
                border-radius: 8px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #D7DEEE;
                background: #FFFFFF;
            }
            QPushButton:hover { background: #F4F7FF; }
            QLabel#productThumb {
                background: #F8FAFF;
                border: 1px solid #E5EAF5;
                border-radius: 10px;
            }
        """)

    def _thumb_placeholder(self, text: str):
        self.thumb.setText(text)
        self.thumb.setPixmap(QPixmap())
        self.thumb.setStyleSheet("""
            QLabel#productThumb {
                background: #F8FAFF;
                border: 1px dashed #D7DEEE;
                border-radius: 10px;
                color: rgba(15,23,42,0.45);
                font-size: 11px;
                font-weight: 600;
            }
        """)

    def _set_thumb_pix(self, pix: QPixmap):
        if pix.isNull():
            self._thumb_placeholder("No Image")
            return

        pix = pix.scaled(
            self.thumb.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.thumb.setText("")
        self.thumb.setStyleSheet("""
            QLabel#productThumb {
                background: #F8FAFF;
                border: 1px solid #E5EAF5;
                border-radius: 10px;
            }
        """)
        self.thumb.setPixmap(pix)

    def _thumb_cache_key(self, product_id: int, target_size: QSize) -> Tuple[int, int, int]:
        return (int(product_id), int(target_size.width()), int(target_size.height()))

    def _target_size_now(self) -> QSize:
        w = max(1, self.thumb.width())
        h = max(1, self.thumb.height())
        return QSize(w, h)

    def _ensure_thumb_loaded(self):
        pid = int(self.product.get("id", 0) or 0)
        has_image = bool(self.product.get("has_image"))

        if not pid or not has_image:
            self._thumb_placeholder("No Image")
            return

        if self.thumb.width() < 40:
            QTimer.singleShot(50, self._ensure_thumb_loaded)
            return

        target_size = self._target_size_now()
        key = self._thumb_cache_key(pid, target_size)

        if key in ProductCard._thumb_cache:
            self._set_thumb_pix(ProductCard._thumb_cache[key])
            return

        self._fetch_thumb_async(pid, target_size)

    def _fetch_thumb_async(self, product_id: int, target_size: QSize):
        existing = self.thumb.pixmap()
        if existing is None or existing.isNull():
            self._thumb_placeholder("Loading...")

        self._request_token += 1
        token = self._request_token
        self._latest_token = token

        gen = ProductCard._current_gen(product_id)

        worker_key = (int(product_id), int(target_size.width()), int(target_size.height()), int(token))
        worker = _FetchThumbWorker(self.api, product_id, gen, token, target_size)
        worker.signals.finished.connect(self._on_thumb_loaded)
        worker.signals.error.connect(self._on_thumb_error)

        self._active_workers[worker_key] = worker
        self.thread_pool.start(worker)

    def _release_worker(self, key: Tuple[int, int, int, int]):
        self._active_workers.pop(key, None)

    def _on_thumb_loaded(self, product_id: int, gen: int, token: int, tw: int, th: int, thumb_img: QImage):
        self._release_worker((int(product_id), int(tw), int(th), int(token)))

        if token != self._latest_token:
            return
        if gen != ProductCard._current_gen(product_id):
            return

        if thumb_img.isNull():
            existing = self.thumb.pixmap()
            if existing is None or existing.isNull():
                self._thumb_placeholder("No Image")
            return

        pix = QPixmap.fromImage(thumb_img)
        pix = _rounded_pixmap(pix, radius=10)

        cache_key = (int(product_id), int(tw), int(th))
        ProductCard._thumb_cache[cache_key] = pix

        current_id = int(self.product.get("id", 0) or 0)
        if current_id == product_id:
            now = self._target_size_now()
            if now.width() == tw and now.height() == th:
                self._set_thumb_pix(pix)

    def _on_thumb_error(self, product_id: int, gen: int, token: int, tw: int, th: int, msg: str):
        self._release_worker((int(product_id), int(tw), int(th), int(token)))

        if token != self._latest_token:
            return
        if gen != ProductCard._current_gen(product_id):
            return

        existing = self.thumb.pixmap()
        if existing is not None and not existing.isNull():
            return

        current_id = int(self.product.get("id", 0) or 0)
        if current_id == product_id:
            self._thumb_placeholder("No Image")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not getattr(self, "_built", False):
            return

        pid = int(self.product.get("id", 0) or 0)
        has_image = bool(self.product.get("has_image"))
        if not pid or not has_image:
            return

        target_size = self._target_size_now()
        key = self._thumb_cache_key(pid, target_size)
        if key not in ProductCard._thumb_cache:
            QTimer.singleShot(120, self._ensure_thumb_loaded)

    def _apply_icon(self, btn: QPushButton, icon_name: str, fallback_text: str):
        icon = get_feather_icon(icon_name, 14)
        if isinstance(icon, QIcon) and not icon.isNull():
            btn.setIcon(icon)
        else:
            btn.setText(fallback_text)
