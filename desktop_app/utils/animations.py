# animations.py
#
# This module provides UI animation utilities for smooth transitions and effects.
# Includes fade animations, slide animations, and hover effects.
#
# Usage: Imported by UI modules to add smooth animations to widgets.

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt6.QtGui import QTransform
from utils.config import AppConfig


def fade_in(widget: QWidget, duration: int = None):
    """
    Fade in a widget using opacity animation.
    
    Args:
        widget: The widget to animate
        duration: Animation duration in milliseconds (defaults to AppConfig.ANIMATION_DURATION)
    """
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


def fade_out(widget: QWidget, duration: int = None, on_finished=None):
    """
    Fade out a widget using opacity animation.
    
    Args:
        widget: The widget to animate
        duration: Animation duration in milliseconds
        on_finished: Callback function to execute when animation finishes
    """
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


def slide_in(widget: QWidget, direction: str = "right", duration: int = None):
    """
    Slide in a widget from a direction.
    
    Args:
        widget: The widget to animate
        direction: Direction to slide from ("left", "right", "top", "bottom")
        duration: Animation duration in milliseconds
    """
    if duration is None:
        duration = AppConfig.ANIMATION_DURATION
    
    parent = widget.parent()
    if not parent:
        return
    
    # Store original position
    original_pos = widget.pos()
    
    # Set initial position based on direction
    if direction == "left":
        widget.move(parent.width(), original_pos.y())
    elif direction == "right":
        widget.move(-widget.width(), original_pos.y())
    elif direction == "top":
        widget.move(original_pos.x(), parent.height())
    elif direction == "bottom":
        widget.move(original_pos.x(), -widget.height())
    
    # Animate to original position
    animation = QPropertyAnimation(widget, b"pos")
    animation.setDuration(duration)
    animation.setStartValue(widget.pos())
    animation.setEndValue(original_pos)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


def slide_out(widget: QWidget, direction: str = "right", duration: int = None, on_finished=None):
    """
    Slide out a widget in a direction.
    
    Args:
        widget: The widget to animate
        direction: Direction to slide to ("left", "right", "top", "bottom")
        duration: Animation duration in milliseconds
        on_finished: Callback function to execute when animation finishes
    """
    if duration is None:
        duration = AppConfig.ANIMATION_DURATION
    
    parent = widget.parent()
    if not parent:
        return
    
    start_pos = widget.pos()
    
    # Calculate end position based on direction
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


def scale_up(widget: QWidget, duration: int = None):
    """
    Scale up a widget from 0.8 to 1.0.
    
    Args:
        widget: The widget to animate
        duration: Animation duration in milliseconds
    """
    if duration is None:
        duration = AppConfig.ANIMATION_DURATION
    
    # Note: This is a simplified version. For proper scaling, you'd need to use
    # QGraphicsScale or transform the widget's geometry
    # For now, this is a placeholder that could be enhanced
    fade_in(widget, duration)


def pulse(widget: QWidget, duration: int = None, loops: int = 2):
    """
    Pulse animation (fade in and out repeatedly).
    
    Args:
        widget: The widget to animate
        duration: Animation duration in milliseconds (for one pulse cycle)
        loops: Number of times to pulse
    """
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
    """
    Setup hover effect for a card widget (slight lift and shadow increase).
    This is typically done via CSS, but can be enhanced with animations.
    
    Args:
        card_widget: The card widget to setup hover effect for
    """
    # This is primarily handled by CSS stylesheets, but could be enhanced
    # with actual transform animations if needed
    pass


def animate_page_transition(old_page: QWidget, new_page: QWidget, direction: str = "right"):
    """
    Animate transition between two pages.
    
    Args:
        old_page: The page to fade out
        new_page: The page to fade in
        direction: Direction of transition
    """
    def show_new():
        new_page.show()
        fade_in(new_page)
    
    fade_out(old_page, on_finished=lambda: (old_page.hide(), show_new()))


def setup_button_press_effect(button: QWidget):
    """
    Setup press effect for a button (slight scale down on press).
    
    Args:
        button: The button widget to setup press effect for
    """
    # This is typically handled by CSS :pressed pseudo-state
    # but could be enhanced with actual scale animations
    pass

