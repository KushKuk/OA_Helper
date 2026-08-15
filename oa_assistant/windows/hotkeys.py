"""
Global hotkey management for Windows desktop integration.
"""
import logging
from typing import Callable, Dict, Optional

from PySide6.QtCore import QObject, QAbstractNativeEventFilter, Signal
from PySide6.QtGui import QWindow
from PySide6.QtWidgets import QApplication

from oa_assistant.core.config import settings
from oa_assistant.core.logging import logger


try:
    import win32api
    import win32con
    import win32gui
except ImportError:
    win32api = None
    win32con = None
    win32gui = None


def _is_win32_available():
    """Check if Win32 API is available."""
    return win32api is not None


class HotkeyManager(QObject, QAbstractNativeEventFilter):
    """
    Manages global hotkeys for Windows desktop applications.
    Uses Win32 API for global hotkey registration and Qt native event filter for WM_HOTKEY.
    """

    # Signal to trigger hotkey actions on the GUI thread
    hotkey_triggered = Signal(str)

    def __init__(self):
        super().__init__()
        self._registered_hotkeys: Dict[str, int] = {}  # action_name -> hotkey_id
        self._hotkey_actions: Dict[str, Callable] = {}  # action_name -> callback
        self._is_registered = False
        self._next_hotkey_id = 0xB000  # Start IDs from 0xB000 to avoid conflicts
        self._window_handle = None  # Window handle to associate hotkeys with
        self._event_filter_installed = False  # Track if we've installed the native event filter

        # Connect signal to thread-safe slot
        self.hotkey_triggered.connect(self._execute_action)

        logger.debug("HotkeyManager initialized")

    def set_window_handle(self, window_handle: int):
        """
        Set the window handle to associate hotkeys with.

        Args:
            window_handle: The window handle (HWND) to associate hotkeys with
        """
        self._window_handle = window_handle
        logger.debug(f"Window handle set to: {window_handle}")

    def _try_install_event_filter(self):
        """Try to install the native event filter if QApplication is available."""
        if not _is_win32_available() or self._event_filter_installed:
            return
        qapp = QApplication.instance()
        if qapp is not None:
            qapp.installNativeEventFilter(self)
            self._event_filter_installed = True
            logger.debug("Native event filter installed")
        else:
            logger.warning("QApplication instance not available for event filter installation")

    def register_hotkey(self, action_name: str, key_combination: str, callback: Callable) -> bool:
        """
        Register a global hotkey.

        Args:
            action_name: Unique identifier for the action
            key_combination: String like "ctrl+space", "ctrl+shift+c"
            callback: Function to call when hotkey is triggered

        Returns:
            bool: True if registration successful, False otherwise
        """
        if not _is_win32_available():
            logger.warning("Win32 API not available, hotkey registration skipped")
            return False

        if action_name in self._registered_hotkeys:
            logger.warning(f"Hotkey for action '{action_name}' already registered")
            return False

        try:
            # Parse key combination
            modifiers, vk_code = self._parse_key_combination(key_combination)
            if modifiers is None or vk_code is None:
                logger.error(f"Invalid key combination: {key_combination}")
                return False

            # Generate unique hotkey ID
            hotkey_id = self._next_hotkey_id
            self._next_hotkey_id += 1

            # Register the hotkey
            logger.debug(f"Attempting to register hotkey: action='{action_name}', combination='{key_combination}', mods={modifiers:04x}, vk={vk_code:02x}, id={hotkey_id:04x}, window_handle={self._window_handle}")
            try:
                result = win32gui.RegisterHotKey(self._window_handle, hotkey_id, modifiers, vk_code)
            except Exception as e:
                logger.error(f"Exception calling RegisterHotKey: {e}")
                return False
            logger.debug(f"RegisterHotKey returned: {result}")
            if result:
                self._registered_hotkeys[action_name] = hotkey_id
                self._hotkey_actions[action_name] = callback
                logger.info(f"Registered hotkey '{key_combination}' for action '{action_name}' (ID: {hotkey_id})")
                return True
            else:
                error_code = win32api.GetLastError()
                logger.error(f"Failed to register hotkey '{key_combination}'. Error code: {error_code} (0x{error_code:04x})")
                # Log additional info for debugging
                logger.error(f"Hotkey params: action='{action_name}', combo='{key_combination}', mods={modifiers}, vk={vk_code}, id={hotkey_id}, window_handle={self._window_handle}")
                # Additional debugging: check if the hotkey ID is already in use
                if error_code == 1409:  # ERROR_HOTKEY_ALREADY_REGISTERED
                    logger.error("Hotkey ID appears to be already registered")
                return False

        except Exception as e:
            logger.error(f"Exception registering hotkey '{key_combination}': {e}")
            return False

    def unregister_hotkey(self, action_name: str) -> bool:
        """
        Unregister a specific hotkey.

        Args:
            action_name: The action name to unregister

        Returns:
            bool: True if unregistration successful, False otherwise
        """
        if not _is_win32_available():
            return False

        if action_name not in self._registered_hotkeys:
            logger.warning(f"Hotkey for action '{action_name}' not registered")
            return False

        try:
            hotkey_id = self._registered_hotkeys[action_name]
            if win32gui.UnregisterHotKey(self._window_handle, hotkey_id):
                del self._registered_hotkeys[action_name]
                del self._hotkey_actions[action_name]
                logger.info(f"Unregistered hotkey for action '{action_name}' (ID: {hotkey_id})")
                return True
            else:
                error_code = win32api.GetLastError()
                logger.error(f"Failed to unregister hotkey for action '{action_name}'. Error code: {error_code}")
                return False
        except Exception as e:
            logger.error(f"Exception unregistering hotkey for action '{action_name}': {e}")
            return False

    def unregister_all(self) -> None:
        """Unregister all registered hotkeys."""
        if not _is_win32_available():
            return

        for action_name in list(self._registered_hotkeys.keys()):
            self.unregister_hotkey(action_name)

        logger.info("All hotkeys unregistered")

    def start(self) -> bool:
        """
        Start the hotkey manager (register all configured hotkeys).

        Returns:
            bool: True if at least one hotkey registered successfully
        """
        if self._is_registered:
            logger.warning("HotkeyManager already started")
            return True

        # Try to install event filter again in case QApplication wasn't available earlier
        self._try_install_event_filter()

        success = False
        # Register configured hotkeys from settings
        if self._register_configured_hotkeys():
            success = True

        self._is_registered = success
        logger.info(f"HotkeyManager started: {success}")
        return success

    def stop(self) -> None:
        """Stop the hotkey manager (unregister all hotkeys)."""
        if not self._is_registered:
            logger.warning("HotkeyManager already stopped")
            return

        self.unregister_all()
        # Remove the native event filter if we installed it
        if self._event_filter_installed and _is_win32_available():
            qapp = QApplication.instance()
            if qapp is not None:
                qapp.removeNativeEventFilter(self)
            self._event_filter_installed = False
            logger.debug("Native event filter removed")

        self._is_registered = False
        logger.info("HotkeyManager stopped")

    def is_registered(self) -> bool:
        """Check if hotkey manager is active."""
        return self._is_registered

    def nativeEventFilter(self, event_type, message):
        """
        Filter native events to catch WM_HOTKEY.
        """
        if event_type == "windows_generic_MSG" or event_type == "windows_dispatcher_MSG":
            # Cast the message to a MSG structure
            from ctypes import wintypes
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0312:  # WM_HOTKEY
                hotkey_id = msg.wParam
                # Find the action for this hotkey ID
                for action_name, hotkey_id_registered in self._registered_hotkeys.items():
                    if hotkey_id_registered == hotkey_id:
                        self.hotkey_triggered.emit(action_name)
                        return True, 0  # We handled the event
        return False, 0

    def _register_configured_hotkeys(self) -> bool:
        """
        Register hotkeys from configuration.

        Returns:
            bool: True if at least one hotkey registered successfully
        """
        success = False

        # Register toggle overlay hotkey
        toggle_hotkey = settings.HOTKEY_TOGGLE_OVERLAY
        if self.register_hotkey("toggle_overlay", toggle_hotkey, self._on_toggle_overlay):
            success = True
        else:
            logger.warning(f"Failed to register toggle overlay hotkey: {toggle_hotkey}")

        # Register capture region hotkey (for future use)
        capture_hotkey = settings.HOTKEY_CAPTURE_REGION
        if self.register_hotkey("capture_region", capture_hotkey, self._on_capture_region):
            success = True
        else:
            logger.warning(f"Failed to register capture region hotkey: {capture_hotkey}")

        return success

    def _parse_key_combination(self, key_combination: str) -> tuple:
        """
        Parse a key combination string into modifiers and virtual key code.

        Args:
            key_combination: String like "ctrl+space", "ctrl+shift+c"

        Returns:
            tuple: (modifiers, vk_code) or (None, None) if invalid
        """
        try:
            parts = key_combination.lower().split('+')
            modifiers = 0
            vk_code = None

            # Map modifier keys
            modifier_map = {
                'ctrl': 0x0002,  # MOD_CONTROL
                'control': 0x0002,
                'alt': 0x0001,   # MOD_ALT
                'shift': 0x0004, # MOD_SHIFT
                'win': 0x0008,   # MOD_WIN
                'command': 0x0008,
                'cmd': 0x0008,
            }

            # Process modifiers
            for part in parts[:-1]:  # All parts except the last one (the key)
                part = part.strip()
                if part in modifier_map:
                    modifiers |= modifier_map[part]
                else:
                    logger.warning(f"Unknown modifier: {part}")
                    return None, None

            # Process the key
            key = parts[-1].strip()
            vk_map = {
                'space': 0x20,   # VK_SPACE
                'enter': 0x0D,   # VK_RETURN
                'return': 0x0D,
                'esc': 0x1B,     # VK_ESCAPE
                'escape': 0x1B,
                'tab': 0x09,     # VK_TAB
                'up': 0x26,      # VK_UP
                'down': 0x28,    # VK_DOWN
                'left': 0x25,    # VK_LEFT
                'right': 0x27,   # VK_RIGHT
                'home': 0x24,    # VK_HOME
                'end': 0x23,     # VK_END
                'pageup': 0x21,  # VK_PRIOR
                'pagedown': 0x22,# VK_NEXT
                'delete': 0x2E,  # VK_DELETE
                'backspace': 0x08,# VK_BACK
                'insert': 0x2D,  # VK_INSERT
                # Function keys
                'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
                'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
                'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
                'f13': 0x7C, 'f14': 0x7D, 'f15': 0x7E, 'f16': 0x7F,
                'f17': 0x80, 'f18': 0x81, 'f19': 0x82, 'f20': 0x83,
                'f21': 0x84, 'f22': 0x85, 'f23': 0x86, 'f24': 0x87,
            }

            # Handle single character keys (a-z, 0-9)
            if len(key) == 1 and key.isalnum():
                vk_code = ord(key.upper())
            elif key in vk_map:
                vk_code = vk_map[key]
            else:
                logger.warning(f"Unknown key: {key}")
                return None, None

            return modifiers, vk_code

        except Exception as e:
            logger.error(f"Error parsing key combination '{key_combination}': {e}")
            return None, None

    def _on_toggle_overlay(self) -> None:
        """Callback for toggle overlay hotkey."""
        logger.info("Toggle overlay hotkey triggered")
        self.hotkey_triggered.emit("toggle_overlay")

    def _on_capture_region(self) -> None:
        """Callback for capture region hotkey (placeholder for future)."""
        logger.info("Capture region hotkey triggered")
        self.hotkey_triggered.emit("capture_region")

    def _execute_action(self, action_name: str) -> None:
        """
        Execute the callback for a given action.
        This method is called on the GUI thread via the signal mechanism.

        Args:
            action_name: The action name to execute
        """
        if action_name in self._hotkey_actions:
            try:
                self._hotkey_actions[action_name]()
            except Exception as e:
                logger.error(f"Error executing hotkey action '{action_name}': {e}")
        else:
            logger.warning(f"No action registered for '{action_name}'")


# Global hotkey manager instance - created but not initialized until QApplication is available
hotkey_manager = HotkeyManager()