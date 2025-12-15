# desktop_app/utils/animations.py
#
# UI animation utilities for smooth transitions and effects.

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect

from desktop_app.utils.config import AppConfig


def fade_in(widget: QWidget, duration: int | None = None):
    """Fade in a widget using opacity animation."""
    if duration is None:
        duration = AppConfig.ANIMATION_DURATION

    opacity_effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(opacity_effect)

    animation = QPropertyAnimation(opacity_effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


def fade_out(widget: QWidget, duration: int | None = None, on_finished=None):
    """Fade out a widget using opacity animation."""
    if duration is None:
        duration = AppConfig.ANIMATION_DURATION

    opacity_effect = widget.graphicsEffect()
    if not opacity_effect:
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)

    animation = QPropertyAnimation(opacity_effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)
    animation.setEasingCurve(QEasingCurve.Type.InCubic)

    if on_finished:
        animation.finished.connect(on_finished)

    animation.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)


def slide_in(widget: QWidget, direction: str = "right", duration: int | None = None):
    """Slide in a widget from a direction."""
    if duration is None:
        duration = AppConfig.ANIMATION_DURATION

    parent = widget.parent()
    if not parent:
        return

    original_pos = widget.pos()

    if direction == "left":
        widget.move(parent.width(), original_pos.y())
    elif direction == "right":
        widget.move(-widget.width(), original_pos.y())
    elif direction == "top":
        widget.move(original_pos.x(), parent.height())
    elif direction == "bottom":
        widget.move(original_pos.x(), -widget.height())

    animation = QPropertyAnimation(widget, b"pos")
    animation.setDuration(duration)
    animation.setStartValue(widget.pos())
    animation.setEndValue(original_pos)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


def slide_out(widget: QWidget, direction: str = "right",
              duration: int | None = None, on_finished=None):
    """Slide out a widget in a direction."""
    if duration is None:
        duration = AppConfig.ANIMATION_DURATION

    parent = widget.parent()
    if not parent:
        return

    start_pos = widget.pos()

    if direction == "left":
        end_pos = (-widget.width(), start_pos.y())
    elif direction == "right":
        end_pos = (parent.width(), start_pos.y())
    elif direction == "top":
        end_pos = (start_pos.x(), -widget.height())
    elif direction == "bottom":
        end_pos = (start_pos.x(), parent.height())
    else:
        end_pos = start_pos

    animation = QPropertyAnimation(widget, b"pos")
    animation.setDuration(duration)
    animation.setStartValue(start_pos)
    animation.setEndValue(end_pos)
    animation.setEasingCurve(QEasingCurve.Type.InCubic)

    if on_finished:
        animation.finished.connect(on_finished)

    animation.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)


def scale_up(widget: QWidget, duration: int | None = None):
    """Placeholder scale-up effect. Uses fade for now."""
    if duration is None:
        duration = AppConfig.ANIMATION_DURATION
    fade_in(widget, duration)


def pulse(widget: QWidget, duration: int | None = None, loops: int = 2):
    """Pulse animation (fade in and out)."""
    if duration is None:
        duration = AppConfig.ANIMATION_DURATION

    opacity_effect = widget.graphicsEffect()
    if not opacity_effect:
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)

    animation = QPropertyAnimation(opacity_effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(1.0)
    animation.setEndValue(0.3)
    animation.setLoopCount(loops)
    animation.setEasingCurve(QEasingCurve.Type.InOutSine)
    animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


def setup_card_hover_effect(card_widget: QWidget):
    """Hover effect is primarily handled by stylesheets."""
    pass


def animate_page_transition(old_page: QWidget, new_page: QWidget, direction: str = "right"):
    """Animate transition between two pages."""
    def show_new():
        new_page.show()
        fade_in(new_page)

    fade_out(old_page, on_finished=lambda: (old_page.hide(), show_new()))


def setup_button_press_effect(button: QWidget):
    """Press effect is typically handled by :pressed styles."""
    pass
