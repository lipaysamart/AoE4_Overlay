import json
from types import TracebackType
from typing import Callable, Optional, Tuple, Type

import keyboard
import requests
from PyQt5 import QtCore, QtGui, QtWidgets

from overlay.i18n import get_language, tr
from overlay.api_checking import find_player, ping_endpoint
from overlay.helper_func import normalize_api_url
from overlay.custom_widgets import CustomKeySequenceEdit
from overlay.logging_func import get_logger
from overlay.overlay_widget import AoEOverlay
from overlay.settings import settings
from overlay.worker import scheldule

logger = get_logger(__name__)


class SettingsTab(QtWidgets.QWidget):
    new_profile = QtCore.pyqtSignal()
    show_hide_overlay = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.overlay_widget = AoEOverlay()
        self._retry_callback: Optional[Callable] = None
        self.init_UI()
        self.show_hide_overlay.connect(self.overlay_widget.show_hide)

    def init_UI(self):
        # Layout
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(25)
        self.setLayout(self.main_layout)

        ### Profile box
        profile_box = QtWidgets.QGroupBox(tr("Profile"))
        profile_box.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                  QtWidgets.QSizePolicy.Fixed))
        profile_box.setMinimumSize(400, 100)
        profile_box_layout = QtWidgets.QGridLayout()
        profile_box.setLayout(profile_box_layout)
        self.main_layout.addWidget(profile_box)

        # Profile info
        self.profile_info = QtWidgets.QLabel(tr("No player identified"))
        self.profile_info.setStyleSheet("font-weight: bold")
        self.profile_info.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse)
        profile_box_layout.addWidget(self.profile_info)

        self.profile_link = QtWidgets.QLabel("")
        self.profile_link.setOpenExternalLinks(True)
        profile_box_layout.addWidget(self.profile_link, 1, 0)

        # Multi search
        self.multi_search = QtWidgets.QLineEdit()
        self.multi_search.setPlaceholderText(tr("Steam ID / Profile ID / Name"))
        self.multi_search.setToolTip(
            tr('Search for your account with one of these (Steam ID / Profile ID / Name).'
               ' Searching by name might not find the correct player.'))
        self.multi_search.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.multi_search.setMaximumWidth(220)
        profile_box_layout.addWidget(self.multi_search, 2, 0)

        # Multi search button
        self.multi_search_btn = QtWidgets.QPushButton(tr("Search"))
        self.multi_search_btn.clicked.connect(self.find_profile)
        self.multi_search_btn.setShortcut("Return")
        self.multi_search_btn.setToolTip(
            tr('Search for your account with one of these (Steam ID / Profile ID / Name).'
               ' Searching by name might not find the correct player.'))
        profile_box_layout.addWidget(self.multi_search_btn, 2, 1)

        # Notification
        self.notification_label = QtWidgets.QLabel()
        self.notification_label.setWordWrap(True)
        profile_box_layout.addWidget(self.notification_label, 3, 0)

        ### Overlay box
        overlay_box = QtWidgets.QGroupBox(tr("Overlay"))
        overlay_box.setMinimumSize(400, 100)
        overlay_box.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                  QtWidgets.QSizePolicy.Fixed))
        overlay_layout = QtWidgets.QGridLayout()
        overlay_box.setLayout(overlay_layout)
        self.main_layout.addWidget(overlay_box)

        # Hotkey for overlay
        key_label = QtWidgets.QLabel(tr("Hotkey for showing and hiding overlay:"))
        overlay_layout.addWidget(key_label, 0, 0)

        self.key_showhide = CustomKeySequenceEdit(self)
        self.key_showhide.setMaximumWidth(100)
        self.key_showhide.setToolTip(tr("Hotkey for showing and hiding overlay"))
        overlay_layout.addWidget(self.key_showhide, 0, 1)
        self.key_showhide.key_changed.connect(self.hotkey_changed)

        # Overlay font
        font_label = QtWidgets.QLabel(tr("Overlay font size:"))
        overlay_layout.addWidget(font_label, 1, 0)

        self.font_size_combo = QtWidgets.QComboBox()
        for i in range(1, 50):
            self.font_size_combo.addItem(f"{i} pt")
        self.font_size_combo.setCurrentIndex(settings.font_size - 1)
        self.font_size_combo.currentIndexChanged.connect(
            self.font_size_changed)
        overlay_layout.addWidget(self.font_size_combo, 1, 1)

        # Position change button
        self.btn_change_position = QtWidgets.QPushButton(
            tr("Change/fix overlay position"))
        self.btn_change_position.setToolTip(
            tr("Click to change overlay position. Click again to fix its position.")
        )
        self.btn_change_position.clicked.connect(
            self.overlay_widget.change_state)
        overlay_layout.addWidget(self.btn_change_position, 2, 0, 1, 2)

        ### API box
        api_box = QtWidgets.QGroupBox(tr("API"))
        api_box.setMinimumWidth(400)
        api_box.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                  QtWidgets.QSizePolicy.Fixed))
        api_layout = QtWidgets.QGridLayout()
        api_box.setLayout(api_layout)
        self.main_layout.addWidget(api_box)

        # Endpoint selector
        api_layout.addWidget(QtWidgets.QLabel(tr("API endpoint:")), 0, 0)
        self.api_combo = QtWidgets.QComboBox()
        self.api_combo.setMinimumWidth(260)
        self.api_combo.currentTextChanged.connect(self.api_endpoint_changed)
        api_layout.addWidget(self.api_combo, 0, 1, 1, 2)
        self.refresh_api_combo()

        # New endpoint input + add button
        self.api_input = QtWidgets.QLineEdit()
        self.api_input.setPlaceholderText("https://example.com/api/v0")
        self.api_input.setFocusPolicy(QtCore.Qt.ClickFocus)
        api_layout.addWidget(self.api_input, 1, 0, 1, 2)

        self.api_add_btn = QtWidgets.QPushButton(tr("Add"))
        self.api_add_btn.clicked.connect(self.add_api_endpoint)
        api_layout.addWidget(self.api_add_btn, 1, 2)

        # Test button, remove button, auto-switch checkbox
        self.api_test_btn = QtWidgets.QPushButton(tr("Test connection"))
        self.api_test_btn.setToolTip(
            tr("Test the connection to the selected API endpoint"))
        self.api_test_btn.clicked.connect(self.test_api_endpoint)
        api_layout.addWidget(self.api_test_btn, 2, 0)

        self.api_auto_checkbox = QtWidgets.QCheckBox(
            tr("Auto-switch endpoint on failure"))
        self.api_auto_checkbox.setToolTip(
            tr("Automatically switch to a backup API endpoint when requests keep failing"))
        self.api_auto_checkbox.setChecked(settings.api_auto_failover)
        self.api_auto_checkbox.stateChanged.connect(
            self.api_auto_failover_changed)
        api_layout.addWidget(self.api_auto_checkbox, 2, 1)

        self.api_remove_btn = QtWidgets.QPushButton(tr("Remove"))
        self.api_remove_btn.clicked.connect(self.remove_api_endpoint)
        api_layout.addWidget(self.api_remove_btn, 2, 2)

        # Language preference is saved now, but translations change on restart.
        language_box = QtWidgets.QGroupBox("Language / 语言")
        language_box.setMinimumWidth(400)
        language_layout = QtWidgets.QVBoxLayout(language_box)
        self.language_combo = QtWidgets.QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("简体中文", "zh_CN")
        self.language_combo.setCurrentIndex(
            self.language_combo.findData(settings.language))
        language_layout.addWidget(self.language_combo)
        self.language_notice = QtWidgets.QLabel()
        self.language_notice.setWordWrap(True)
        language_layout.addWidget(self.language_notice)
        self.language_combo.currentIndexChanged.connect(self.language_changed)
        self.main_layout.addWidget(language_box)

        ### Messages
        msg_layout = QtWidgets.QHBoxLayout()
        self.msg = QtWidgets.QLabel()
        self.msg.setOpenExternalLinks(True)
        self.msg.setWordWrap(True)
        msg_layout.addWidget(self.msg, 1)

        # Retry button (shown only when a request fails)
        self.retry_button = QtWidgets.QPushButton(tr("Retry"))
        self.retry_button.setMaximumWidth(100)
        self.retry_button.setToolTip(tr("Retry the last failed request"))
        self.retry_button.clicked.connect(self.retry_last_action)
        self.retry_button.hide()
        msg_layout.addWidget(self.retry_button)
        self.main_layout.addLayout(msg_layout)

        # Create update button
        self.update_button = QtWidgets.QPushButton(tr("New update!"))
        self.update_button.setMaximumWidth(400)
        self.update_button.setToolTip(tr("Click here to download new app version"))
        self.update_button.setStyleSheet(
            'background-color: #3bb825; color: black')
        self.update_button.hide()
        self.main_layout.addWidget(self.update_button)

    def language_changed(self, index: int):
        previous = settings.language
        settings.language = self.language_combo.itemData(index)
        try:
            settings.save()
        except Exception:
            logger.exception("Failed to save language preference")
            settings.language = previous
            self.language_combo.blockSignals(True)
            try:
                self.language_combo.setCurrentIndex(
                    self.language_combo.findData(previous))
            finally:
                self.language_combo.blockSignals(False)
            self.language_notice.setText(tr("Failed to save the language preference."))
            return
        self.language_notice.setText(
            tr("Restart the app to apply the language change.")
            if settings.language != get_language() else "")

    def start(self):
        # Initialize
        self.update_profile_info()
        self.init_hotkeys()

        if settings.steam_id or settings.profile_id:
            self.new_profile.emit()

    def init_hotkeys(self):
        if settings.overlay_hotkey:
            try:
                self.key_showhide.setKeySequence(
                    QtGui.QKeySequence.fromString(settings.overlay_hotkey))
                keyboard.add_hotkey(settings.overlay_hotkey,
                                    self.show_hide_overlay.emit)
            except Exception:
                logger.exception("Failed to set hotkey")
                settings.overlay_hotkey = ""
                self.key_showhide.setKeySequence(
                    QtGui.QKeySequence.fromString(""))

    def update_profile_info(self):
        """ Updates profile information based on found steam_id and profile_id"""
        s = []
        if settings.player_name:
            s.append(settings.player_name)
        if settings.steam_id:
            s.append(tr("Steam_id: {steam_id}", steam_id=settings.steam_id))
        if settings.profile_id:
            s.append(tr("Profile_id: {profile_id}", profile_id=settings.profile_id))

        if s:
            self.profile_info.setText('\n'.join(s))
            self.profile_info.setStyleSheet(
                "color: #359c20; font-weight: bold")
            self.profile_link.setText(
                f'<a href="https://aoe4world.com/players/{settings.profile_id}">{tr("AoE4 World profile")}</a>'
            )
        else:
            self.profile_info.setText(tr("No player identified"))
            self.profile_link.setText("")

    def notification(self, text: str, color: str = "black"):
        """ Shows a notification"""
        self.notification_label.setText(text)
        self.notification_label.setStyleSheet(f"color: {color}")

    def message(self, text: str, color: str = "black"):
        """ Shows a message"""
        self.msg.setText(text)
        self.msg.setStyleSheet(f"color: {color}")
        if not text:
            # Clearing the message also clears any pending retry action
            self._retry_callback = None
            self.retry_button.hide()

    def aoe4net_error_msg(self,
                          retry_callback: Optional[Callable] = None,
                          endpoint: str = ""):
        """ Shows an API error message, optionally with a retry button """
        self.message(
            tr('Cannot reach the API endpoint ({endpoint}).<br>'
               'Check your network or proxy, or switch to a backup API endpoint below.',
               endpoint=endpoint or settings.api_base_url),
            color='red')
        self._retry_callback = retry_callback
        self.retry_button.setVisible(retry_callback is not None)

    def refresh_api_combo(self):
        """ Reloads the endpoint selector from settings """
        if settings.api_base_url not in settings.api_base_urls:
            settings.api_base_urls.append(settings.api_base_url)
        self.api_combo.blockSignals(True)
        self.api_combo.clear()
        self.api_combo.addItems(settings.api_base_urls)
        self.api_combo.setCurrentText(settings.api_base_url)
        self.api_combo.blockSignals(False)

    def api_endpoint_changed(self, text: str):
        """ Switches the active API endpoint """
        text = text.strip()
        if not text or text == settings.api_base_url:
            return
        if text not in settings.api_base_urls:
            return
        settings.api_base_url = text
        try:
            settings.save()
        except Exception:
            logger.exception("Failed to save settings")
        logger.info(f"API endpoint switched to: {text}")
        self.notification(tr("API endpoint switched"), "#359c20")

    def add_api_endpoint(self):
        """ Adds a new backup API endpoint """
        url = normalize_api_url(self.api_input.text())
        if not url:
            self.notification(tr("Invalid address"), "red")
            return
        if url not in settings.api_base_urls:
            settings.api_base_urls.append(url)
        settings.api_base_url = url
        try:
            settings.save()
        except Exception:
            logger.exception("Failed to save settings")
        self.api_input.setText("")
        self.refresh_api_combo()
        logger.info(f"API endpoint added: {url}")
        self.notification(tr("Endpoint added"), "#359c20")

    def remove_api_endpoint(self):
        """ Removes the selected API endpoint """
        url = self.api_combo.currentText().strip()
        if len(settings.api_base_urls) <= 1:
            self.notification(tr("Keep at least one endpoint"), "red")
            return
        if url in settings.api_base_urls:
            settings.api_base_urls.remove(url)
        if settings.api_base_url == url:
            settings.api_base_url = settings.api_base_urls[0]
        try:
            settings.save()
        except Exception:
            logger.exception("Failed to save settings")
        self.refresh_api_combo()
        logger.info(f"API endpoint removed: {url}")
        self.notification(tr("Endpoint removed"), "#359c20")

    def api_auto_failover_changed(self, state: int):
        settings.api_auto_failover = bool(state)
        try:
            settings.save()
        except Exception:
            logger.exception("Failed to save settings")

    def test_api_endpoint(self):
        """ Tests the connection to the selected API endpoint """
        url = self.api_combo.currentText().strip()
        if not url:
            return
        self.api_test_btn.setEnabled(False)
        self.notification(tr("Testing connection..."))
        scheldule(self.test_api_done,
                  ping_endpoint,
                  url,
                  error_callback=self.test_api_error)

    def test_api_done(self, latency_ms: int):
        self.api_test_btn.setEnabled(True)
        self.notification(tr("Connection OK ({latency} ms)", latency=latency_ms),
                          "#359c20")

    def test_api_error(self, exc_data: Tuple[Type[BaseException], Exception,
                                             TracebackType]):
        self.api_test_btn.setEnabled(True)
        exctype, value, formatted = exc_data
        logger.warning(f"API endpoint test failed\n{formatted}")
        self.notification(tr("Connection failed"), "red")

    def retry_last_action(self):
        """ Retries the last failed request """
        callback = self._retry_callback
        self.message("")
        if callback is not None:
            logger.info("Retrying the last failed request")
            callback()

    def find_profile(self):
        """ Attempts to find player ids based on provided text (name, either id)"""
        self.notification_label.setText("")
        text = self.multi_search.text().strip()
        if not text:
            return
        logger.info(f"Finding a player with key: {text}")

        scheldule(self.find_profile_finish,
                  find_player,
                  text,
                  error_callback=self.error_when_finding_profile)

    def error_when_finding_profile(self,
                                   exc_data: Tuple[Type[BaseException],
                                                   Exception, TracebackType]):
        """ Invalid responses and failed requests when finding a player profile
        indicate an issue with the API servers or the connection"""
        exctype, value, formatted = exc_data
        if issubclass(exctype, (json.decoder.JSONDecodeError,
                                requests.RequestException)):
            self.aoe4net_error_msg(retry_callback=self.find_profile)
            logger.warning(
                f"API error when finding a player\n{formatted}")
        else:
            logger.warning(formatted)

    def find_profile_finish(self, result: bool):
        if result:
            self.new_profile.emit()
            self.update_profile_info()
            self.notification(tr("Player found!"), "#359c20")
        else:
            self.notification(tr("Failed to find such player!"), "red")

    def font_size_changed(self):
        font_size = self.font_size_combo.currentIndex() + 1
        settings.font_size = font_size
        self.overlay_widget.update_style(font_size)

    def hotkey_changed(self, new_hotkey: str):
        """ Checks whether the hotkey is actually new and valid.
        Updates keyboard threads"""
        old_hotkey = settings.overlay_hotkey
        new_hotkey = CustomKeySequenceEdit.convert_hotkey(new_hotkey)

        if new_hotkey == "Del":
            self.key_showhide.setKeySequence(QtGui.QKeySequence.fromString(""))
            settings.overlay_hotkey = ""
            return
        elif not new_hotkey or new_hotkey == settings.overlay_hotkey:
            return

        try:
            keyboard.add_hotkey(new_hotkey, self.show_hide_overlay.emit)
            if settings.overlay_hotkey:
                keyboard.remove_hotkey(settings.overlay_hotkey)
            settings.overlay_hotkey = new_hotkey
            logger.info(f"Setting new hotkey to: {new_hotkey}")
        except Exception:
            logger.exception(f"Failed to set hotkey: {new_hotkey}")
            self.message(tr("Failed to use this hotkey"), color='red')
            self.key_showhide.setKeySequence(
                QtGui.QKeySequence.fromString(old_hotkey))
