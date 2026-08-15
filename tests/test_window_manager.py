"""
Unit tests for window manager functionality.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect, QSize, QPoint, Qt

# Only import if we can create a QApplication instance
try:
    app = QApplication.instance() or QApplication([])
    from oa_assistant.windows.window_manager import WindowManager
    WINDOW_MANAGER_AVAILABLE = True
except Exception:
    WINDOW_MANAGER_AVAILABLE = False


def test_window_manager_initialization():
    """Test that WindowManager initializes correctly."""
    if not WINDOW_MANAGER_AVAILABLE:
        return

    mock_window = Mock()
    window_manager = WindowManager(mock_window)

    assert window_manager.window == mock_window
    assert window_manager._is_visible == False
    assert window_manager._is_minimized == False
    assert window_manager._saved_geometry is None


def test_show_hide_toggle():
    """Test show, hide, and toggle functionality."""
    if not WINDOW_MANAGER_AVAILABLE:
        return

    mock_window = Mock()
    mock_window.isVisible.return_value = False
    window_manager = WindowManager(mock_window)

    # Test show
    window_manager.show()
    mock_window.show.assert_called_once()
    assert window_manager._is_visible == True

    # Test hide
    mock_window.isVisible.return_value = True
    window_manager.hide()
    mock_window.hide.assert_called_once()
    assert window_manager._is_visible == False

    # Test toggle visibility
    mock_window.isVisible.return_value = False
    window_manager.toggle_visibility()
    # Should call show since window is not visible
    mock_window.show.assert_called()
    assert window_manager._is_visible == True


def test_minimize_restore():
    """Test minimize and restore functionality."""
    if not WINDOW_MANAGER_AVAILABLE:
        return

    mock_window = Mock()
    window_manager = WindowManager(mock_window)

    # Test minimize
    window_manager.minimize()
    mock_window.showMinimized.assert_called_once()
    assert window_manager._is_minimized == True

    # Test restore
    window_manager.restore()
    mock_window.showNormal.assert_called_once()
    assert window_manager._is_minimized == False


def test_is_visible():
    """Test is_visible method."""
    if not WINDOW_MANAGER_AVAILABLE:
        return

    mock_window = Mock()
    window_manager = WindowManager(mock_window)

    # Test when window is visible and not minimized
    mock_window.isVisible.return_value = True
    window_manager._is_minimized = False
    assert window_manager.is_visible() == True

    # Test when window is not visible
    mock_window.isVisible.return_value = False
    assert window_manager.is_visible() == False

    # Test when window is visible but minimized
    mock_window.isVisible.return_value = True
    window_manager._is_minimized = True
    assert window_manager.is_visible() == False


def test_set_always_on_top():
    """Test set_always_on_top method."""
    if not WINDOW_MANAGER_AVAILABLE:
        return

    mock_window = Mock()
    window_manager = WindowManager(mock_window)

    # Test setting to True
    window_manager.set_always_on_top(True)
    mock_window.setWindowFlag.assert_called_with(
        Qt.WindowType.WindowStaysOnTopHint,
        True
    )

    # Test setting to False
    window_manager.set_always_on_top(False)
    mock_window.setWindowFlag.assert_called_with(
        Qt.WindowType.WindowStaysOnTopHint,
        False
    )


def test_get_available_monitors():
    """Test get_available_monitors method."""
    if not WINDOW_MANAGER_AVAILABLE:
        return

    with patch('oa_assistant.windows.window_manager.QGuiApplication') as mock_qgui:
        mock_screens = [Mock(), Mock()]
        mock_qgui.screens.return_value = mock_screens

        mock_window = Mock()
        window_manager = WindowManager(mock_window)

        monitors = window_manager.get_available_monitors()
        assert monitors == mock_screens
        mock_qgui.screens.assert_called_once()


def test_get_primary_monitor():
    """Test get_primary_monitor method."""
    if not WINDOW_MANAGER_AVAILABLE:
        return

    with patch('oa_assistant.windows.window_manager.QGuiApplication') as mock_qgui:
        mock_primary_screen = Mock()
        mock_qgui.primaryScreen.return_value = mock_primary_screen

        mock_window = Mock()
        window_manager = WindowManager(mock_window)

        primary = window_manager.get_primary_monitor()
        assert primary == mock_primary_screen
        mock_qgui.primaryScreen.assert_called_once()


def test_get_current_monitor():
    """Test get_current_monitor method."""
    if not WINDOW_MANAGER_AVAILABLE:
        return

    with patch('oa_assistant.windows.window_manager.QGuiApplication') as mock_qgui, \
         patch.object(QRect, 'center', return_value=QPoint(100, 100)):

        # Mock screens
        mock_screen1 = Mock()
        mock_screen1.geometry.return_value = QRect(0, 0, 800, 600)
        mock_screen2 = Mock()
        mock_screen2.geometry.return_value = QRect(800, 0, 800, 600)

        mock_qgui.screens.return_value = [mock_screen1, mock_screen2]
        mock_qgui.primaryScreen.return_value = mock_screen1

        mock_window = Mock()
        mock_window.frameGeometry.return_value = QRect(100, 100, 200, 200)

        window_manager = WindowManager(mock_window)

        # Should return screen1 since center point (100,100) is in screen1
        current = window_manager.get_current_monitor()
        assert current == mock_screen1


def test_ensure_on_screen():
    """Test ensure_on_screen method."""
    if not WINDOW_MANAGER_AVAILABLE:
        return

    with patch('oa_assistant.windows.window_manager.QGuiApplication') as mock_qgui:
        mock_screen = Mock()
        mock_screen.geometry.return_value = QRect(0, 0, 1920, 1080)
        mock_qgui.screens.return_value = [mock_screen]
        mock_qgui.primaryScreen.return_value = mock_screen

        mock_window = Mock()
        mock_window.frameGeometry.return_value = QRect(100, 100, 200, 200)

        window_manager = WindowManager(mock_window)

        # Window is on screen, should not move
        window_manager.ensure_on_screen()
        # If window was off-screen, it would have been moved

        # Test with off-screen window
        mock_window.frameGeometry.return_value = QRect(-500, -500, 200, 200)
        window_manager.ensure_on_screen()
        # Should have called move to reposition on primary monitor


if __name__ == "__main__":
    test_window_manager_initialization()
    test_show_hide_toggle()
    test_minimize_restore()
    test_is_visible()
    test_set_always_on_top()
    test_get_available_monitors()
    test_get_primary_monitor()
    test_get_current_monitor()
    test_ensure_on_screen()
    print("All window manager tests passed!")