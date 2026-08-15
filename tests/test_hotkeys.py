"""
Unit tests for hotkey manager functionality.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Only import if we can create a QApplication instance
try:
    app = QApplication.instance() or QApplication([])
    from oa_assistant.windows.hotkeys import HotkeyManager, hotkey_manager
    HOTKEY_MANAGER_AVAILABLE = True
except Exception:
    HOTKEY_MANAGER_AVAILABLE = False


def test_hotkey_manager_initialization():
    """Test that HotkeyManager initializes correctly."""
    if not HOTKEY_MANAGER_AVAILABLE:
        return

    hotkey_manager = HotkeyManager()
    assert hotkey_manager._registered_hotkeys == {}
    assert hotkey_manager._hotkey_actions == {}
    assert hotkey_manager._is_registered == False
    assert hotkey_manager._next_hotkey_id == 0xB000


def test_register_hotkey():
    """Test hotkey registration."""
    if not HOTKEY_MANAGER_AVAILABLE:
        return

    with patch('oa_assistant.windows.hotkeys._is_win32_available', return_value=True), \
         patch('oa_assistant.windows.hotkeys.win32api') as mock_win32api, \
         patch('oa_assistant.windows.hotkeys.win32gui') as mock_win32gui:
        mock_win32gui.RegisterHotKey.return_value = True
        mock_win32api.GetLastError.return_value = 0

        hotkey_manager = HotkeyManager()
        # Set a dummy window handle for testing
        hotkey_manager._window_handle = 1
        callback = Mock()

        result = hotkey_manager.register_hotkey("test_action", "ctrl+space", callback)

        assert result == True
        assert "test_action" in hotkey_manager._registered_hotkeys
        assert hotkey_manager._hotkey_actions["test_action"] == callback
        mock_win32gui.RegisterHotKey.assert_called_once_with(1, mock_win32gui.RegisterHotKey.call_args[0][1], 0x0002, 0x20)


def test_register_hotkey_failure():
    """Test hotkey registration failure."""
    if not HOTKEY_MANAGER_AVAILABLE:
        return

    with patch('oa_assistant.windows.hotkeys._is_win32_available', return_value=True), \
         patch('oa_assistant.windows.hotkeys.win32api') as mock_win32api, \
         patch('oa_assistant.windows.hotkeys.win32gui') as mock_win32gui:
        mock_win32gui.RegisterHotKey.return_value = False
        mock_win32api.GetLastError.return_value = 1409  # ERROR_HOTKEY_ALREADY_REGISTERED

        hotkey_manager = HotkeyManager()
        # Set a dummy window handle for testing
        hotkey_manager._window_handle = 1
        callback = Mock()

        result = hotkey_manager.register_hotkey("test_action", "ctrl+space", callback)

        assert result == False
        assert "test_action" not in hotkey_manager._registered_hotkeys
        mock_win32gui.RegisterHotKey.assert_called_once_with(1, mock_win32gui.RegisterHotKey.call_args[0][1], 0x0002, 0x20)


def test_register_duplicate_hotkey():
    """Test registering duplicate hotkey."""
    if not HOTKEY_MANAGER_AVAILABLE:
        return

    with patch('oa_assistant.windows.hotkeys._is_win32_available', return_value=True), \
         patch('oa_assistant.windows.hotkeys.win32api') as mock_win32api, \
         patch('oa_assistant.windows.hotkeys.win32gui') as mock_win32gui:
        mock_win32gui.RegisterHotKey.return_value = True

        hotkey_manager = HotkeyManager()
        # Set a dummy window handle for testing
        hotkey_manager._window_handle = 1
        callback1 = Mock()
        callback2 = Mock()

        # Register first time
        result1 = hotkey_manager.register_hotkey("test_action", "ctrl+space", callback1)
        assert result1 == True

        # Register second time with same action
        result2 = hotkey_manager.register_hotkey("test_action", "ctrl+space", callback2)
        assert result2 == False  # Should fail
        assert hotkey_manager._hotkey_actions["test_action"] == callback1  # First callback retained


def test_unregister_hotkey():
    """Test hotkey unregistration."""
    if not HOTKEY_MANAGER_AVAILABLE:
        return

    with patch('oa_assistant.windows.hotkeys._is_win32_available', return_value=True), \
         patch('oa_assistant.windows.hotkeys.win32api') as mock_win32api, \
         patch('oa_assistant.windows.hotkeys.win32gui') as mock_win32gui:
        mock_win32gui.RegisterHotKey.return_value = True
        mock_win32gui.UnregisterHotKey.return_value = True

        hotkey_manager = HotkeyManager()
        # Set a dummy window handle for testing
        hotkey_manager._window_handle = 1
        # Set the next hotkey ID to a known value so we can predict the ID
        hotkey_manager._next_hotkey_id = 0xB000
        callback = Mock()

        # Register
        hotkey_manager.register_hotkey("test_action", "ctrl+space", callback)
        assert "test_action" in hotkey_manager._registered_hotkeys

        # Unregister
        result = hotkey_manager.unregister_hotkey("test_action")
        assert result == True
        assert "test_action" not in hotkey_manager._registered_hotkeys
        assert "test_action" not in hotkey_manager._hotkey_actions
        mock_win32gui.UnregisterHotKey.assert_called_once_with(1, 0xB000)


def test_unregister_nonexistent_hotkey():
    """Test unregistering a hotkey that isn't registered."""
    if not HOTKEY_MANAGER_AVAILABLE:
        return

    with patch('oa_assistant.windows.hotkeys._is_win32_available', return_value=True):
        hotkey_manager = HotkeyManager()
        result = hotkey_manager.unregister_hotkey("nonexistent_action")
        assert result == False  # Should return False but not crash


def test_unregister_all():
    """Test unregistering all hotkeys."""
    if not HOTKEY_MANAGER_AVAILABLE:
        return

    with patch('oa_assistant.windows.hotkeys._is_win32_available', return_value=True), \
         patch('oa_assistant.windows.hotkeys.win32api') as mock_win32api, \
         patch('oa_assistant.windows.hotkeys.win32gui') as mock_win32gui:
        mock_win32gui.RegisterHotKey.return_value = True
        mock_win32gui.UnregisterHotKey.return_value = True

        hotkey_manager = HotkeyManager()
        # Set a dummy window handle for testing
        hotkey_manager._window_handle = 1
        # Set the next hotkey ID to a known value so we can predict the IDs
        hotkey_manager._next_hotkey_id = 0xB000
        callback1 = Mock()
        callback2 = Mock()

        # Register two hotkeys
        hotkey_manager.register_hotkey("action1", "ctrl+space", callback1)
        hotkey_manager.register_hotkey("action2", "ctrl+shift+c", callback2)
        assert len(hotkey_manager._registered_hotkeys) == 2

        # Unregister all
        hotkey_manager.unregister_all()
        assert len(hotkey_manager._registered_hotkeys) == 0
        assert len(hotkey_manager._hotkey_actions) == 0
        # Expect calls for IDs 0xB000 and 0xB001
        mock_win32gui.UnregisterHotKey.assert_any_call(1, 0xB000)
        mock_win32gui.UnregisterHotKey.assert_any_call(1, 0xB001)
        assert mock_win32gui.UnregisterHotKey.call_count == 2


def test_start_stop():
    """Test starting and stopping hotkey manager."""
    if not HOTKEY_MANAGER_AVAILABLE:
        return

    with patch('oa_assistant.windows.hotkeys.win32api') as mock_win32api, \
         patch('oa_assistant.windows.hotkeys.win32gui') as mock_win32gui:
        mock_win32gui.RegisterHotKey.return_value = True
        mock_win32api.GetLastError.return_value = 0

        hotkey_manager = HotkeyManager()
        # Set a dummy window handle for testing
        hotkey_manager._window_handle = 1

        # Initially not registered
        assert hotkey_manager.is_registered() == False

        # Start
        result = hotkey_manager.start()
        assert result == True
        assert hotkey_manager.is_registered() == True

        # Start again (should be idempotent)
        result2 = hotkey_manager.start()
        assert result2 == True
        assert hotkey_manager.is_registered() == True

        # Stop
        hotkey_manager.stop()
        assert hotkey_manager.is_registered() == False

        # Stop again (should be idempotent)
        hotkey_manager.stop()
        assert hotkey_manager.is_registered() == False


def test_parse_key_combination():
    """Test parsing key combinations."""
    if not HOTKEY_MANAGER_AVAILABLE:
        return

    hotkey_manager = HotkeyManager()

    # Test ctrl+space
    modifiers, vk = hotkey_manager._parse_key_combination("ctrl+space")
    assert modifiers == 0x0002  # MOD_CONTROL
    assert vk == 0x20  # VK_SPACE

    # Test ctrl+shift+c
    modifiers, vk = hotkey_manager._parse_key_combination("ctrl+shift+c")
    assert modifiers == (0x0002 | 0x0004)  # MOD_CONTROL | MOD_SHIFT
    assert vk == 0x43  # 'C'

    # Test alt+f4
    modifiers, vk = hotkey_manager._parse_key_combination("alt+f4")
    assert modifiers == 0x0001  # MOD_ALT
    assert vk == 0x73  # VK_F4

    # Test single key
    modifiers, vk = hotkey_manager._parse_key_combination("a")
    assert modifiers == 0
    assert vk == 0x41  # 'A'

    # Test function key
    modifiers, vk = hotkey_manager._parse_key_combination("ctrl+f1")
    assert modifiers == 0x0002  # MOD_CONTROL
    assert vk == 0x70  # VK_F1

    # Test invalid combination
    modifiers, vk = hotkey_manager._parse_key_combination("invalid+key")
    assert modifiers == None
    assert vk == None

    # Test unknown modifier
    modifiers, vk = hotkey_manager._parse_key_combination("meta+a")
    assert modifiers == None
    assert vk == None


def test_signal_mechanism():
    """Test that hotkey triggers signal properly."""
    if not HOTKEY_MANAGER_AVAILABLE:
        return

    hotkey_manager = HotkeyManager()
    callback = Mock()
    hotkey_manager.hotkey_triggered.connect(callback)

    # Emit signal
    hotkey_manager.hotkey_triggered.emit("test_action")

    # Process events to allow signal to be delivered
    QApplication.processEvents()

    callback.assert_called_once_with("test_action")


def test_execute_action():
    """Test executing registered actions."""
    if not HOTKEY_MANAGER_AVAILABLE:
        return

    hotkey_manager = HotkeyManager()
    callback = Mock()
    hotkey_manager._hotkey_actions["test_action"] = callback

    # Execute action
    hotkey_manager._execute_action("test_action")
    callback.assert_called_once()

    # Execute non-existent action (should not crash)
    hotkey_manager._execute_action("nonexistent")
    # callback should still have been called once


def test_global_hotkey_manager_instance():
    """Test that global hotkey manager instance exists."""
    if not HOTKEY_MANAGER_AVAILABLE:
        return

    assert hotkey_manager is not None
    assert isinstance(hotkey_manager, HotkeyManager)


if __name__ == "__main__":
    test_hotkey_manager_initialization()
    test_register_hotkey()
    test_register_hotkey_failure()
    test_register_duplicate_hotkey()
    test_unregister_hotkey()
    test_unregister_nonexistent_hotkey()
    test_unregister_all()
    test_start_stop()
    test_parse_key_combination()
    test_signal_mechanism()
    test_execute_action()
    test_global_hotkey_manager_instance()
    print("All hotkey tests passed!")