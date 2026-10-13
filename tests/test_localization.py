"""Run with: python -m unittest discover -s tests -v.

Qt checks use temporary settings, mocked background work, and no keyboard hooks.
"""

import copy
import importlib.util
import json
import logging
import os
from pathlib import Path
from string import Formatter
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from overlay import i18n

HAS_GUI_DEPS = all(importlib.util.find_spec(name) is not None for name in
                   ("PyQt5", "appdirs", "keyboard", "requests", "websockets"))


class TranslationTests(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("en")

    def test_default_invalid_and_missing_translations(self):
        for preference in (None, "", "fr", [], 0, "en"):
            i18n.set_language(preference)
            self.assertEqual(i18n.tr("Settings"), "Settings")
        i18n.set_language("zh_CN")
        self.assertEqual(i18n.tr("Settings"), "设置")
        self.assertEqual(i18n.tr("Uncatalogued text {value}", value="原文"),
                         "Uncatalogued text 原文")

    def test_named_values_and_header_context(self):
        i18n.set_language("zh_CN")
        self.assertEqual(i18n.tr("Team {number}", number=2), "队伍 2")
        self.assertEqual(i18n.tr("Games"), "历史对局")
        self.assertEqual(i18n.tr("Games", context="stats"), "对局数")
        i18n.set_language("en")
        self.assertEqual(i18n.tr("Games", context="stats"), "Games")

    def test_translation_templates_preserve_placeholders(self):
        def fields(text):
            return {name for _, name, _, _ in Formatter().parse(text)
                    if name is not None}
        for catalog in i18n.TRANSLATIONS.values():
            for source, translated in catalog.items():
                with self.subTest(source=source):
                    self.assertEqual(fields(source), fields(translated))


@unittest.skipUnless(HAS_GUI_DEPS, "Install requirements.txt for Qt integration checks")
class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # logging_func creates its files at import time: keep them out of user data.
        cls.module_temp = tempfile.TemporaryDirectory(prefix="aoe4-tests-")
        cls.data_patch = patch("appdirs.user_data_dir", return_value=cls.module_temp.name)
        cls.data_patch.start()
        from PyQt5 import QtCore, QtWidgets
        from overlay import helper_func, settings as settings_module
        cls.QtCore, cls.QtWidgets = QtCore, QtWidgets
        cls.settings_module = settings_module
        cls.settings = settings_module.settings
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.resource_patch = patch.object(helper_func, "ROOT", ROOT / "src")
        cls.resource_patch.start()
        old_hook = sys.excepthook
        try:
            import AoE4_Overlay
            cls.main_class = AoE4_Overlay.MainApp
        finally:
            sys.excepthook = old_hook

    @classmethod
    def tearDownClass(cls):
        cls.resource_patch.stop()
        cls.data_patch.stop()
        for name, logger in logging.Logger.manager.loggerDict.items():
            if (name.startswith("overlay.") or name == "AoE4_Overlay") and isinstance(logger, logging.Logger):
                for handler in list(logger.handlers):
                    handler.close()
                    logger.removeHandler(handler)
        cls.module_temp.cleanup()

    def setUp(self):
        self.original_settings = copy.deepcopy(self.settings.__dict__)
        self.settings.__dict__.clear()
        self.settings.__dict__.update(self.settings_module._Settings().__dict__)
        self.temp = tempfile.TemporaryDirectory(prefix="aoe4-config-")
        self.config_path = Path(self.temp.name) / "config.json"
        self.config_patch = patch.object(self.settings_module, "CONFIG_FILE", str(self.config_path))
        self.config_patch.start()
        i18n.set_language("en")
        self.windows = []

    def tearDown(self):
        for window in self.windows:
            tabs = window.centralWidget()
            tabs.settigns_tab.overlay_widget.close()
            tabs.build_order_tab.overlay.close()
            window.close()
            window.deleteLater()
        self.app.processEvents()
        self.config_patch.stop()
        self.temp.cleanup()
        self.settings.__dict__.clear()
        self.settings.__dict__.update(self.original_settings)
        i18n.set_language("en")

    def window(self, language):
        self.settings.language = language
        i18n.set_language(language)
        with patch("overlay.tab_main.TabWidget.start") as start, \
                patch("keyboard.add_hotkey") as hotkey, \
                patch("requests.sessions.Session.request") as request:
            window = self.main_class()
            start.assert_called_once()
            hotkey.assert_not_called()
            request.assert_not_called()
        self.windows.append(window)
        self.app.processEvents()
        return window

    def test_legacy_and_invalid_configs_default_to_english(self):
        for config in ({"player_name": "玩家原文"}, {"language": "invalid"},
                       {"language": None}, {"language": []}, {"language": "zh_CN"}):
            with self.subTest(config=config):
                self.config_path.write_text(json.dumps(config), encoding="utf-8")
                loaded = self.settings_module._Settings()
                loaded.load()
                self.assertEqual(loaded.language,
                                 "zh_CN" if config.get("language") == "zh_CN" else "en")

    def test_language_saved_immediately_but_applied_only_on_restart(self):
        window = self.window("en")
        page = window.centralWidget().settigns_tab
        page.language_combo.setCurrentIndex(1)
        self.assertEqual(json.loads(self.config_path.read_text())["language"], "zh_CN")
        self.assertEqual(i18n.get_language(), "en")
        self.assertEqual(page.multi_search_btn.text(), "Search")
        self.assertIn("Restart", page.language_notice.text())
        self.settings.load()
        restarted = self.window(self.settings.language)
        self.assertEqual(restarted.centralWidget().settigns_tab.multi_search_btn.text(), "搜索")
        page = restarted.centralWidget().settigns_tab
        page.language_combo.setCurrentIndex(0)
        self.assertIn("重启", page.language_notice.text())
        self.assertEqual(i18n.get_language(), "zh_CN")

    def test_returning_to_running_language_clears_restart_notice(self):
        page = self.window("en").centralWidget().settigns_tab
        page.language_combo.setCurrentIndex(1)
        page.language_combo.setCurrentIndex(0)
        self.assertEqual(page.language_notice.text(), "")
        self.assertEqual(json.loads(self.config_path.read_text())["language"], "en")

    def test_failed_save_restores_preference_and_selector(self):
        page = self.window("en").centralWidget().settigns_tab
        with patch.object(self.settings, "save", side_effect=OSError("read-only")), \
                self.assertLogs("overlay.tab_settings", level="ERROR"):
            page.language_combo.setCurrentIndex(1)
        self.assertEqual(self.settings.language, "en")
        self.assertEqual(page.language_combo.currentData(), "en")
        self.assertEqual(i18n.get_language(), "en")
        self.assertIn("Failed to save", page.language_notice.text())

    def test_desktop_labels_and_overlay_boundary(self):
        for language, tab_names, search in (
                ("en", ["Settings", "Games", "Build orders", "Randomize", "Override"], "Search"),
                ("zh_CN", ["设置", "历史对局", "建造顺序", "随机选择", "手动覆盖"], "搜索")):
            with self.subTest(language=language):
                window = self.window(language)
                tabs = window.centralWidget()
                self.assertEqual([tabs.tabText(i) for i in range(tabs.count())], tab_names)
                self.assertEqual(tabs.settigns_tab.multi_search_btn.text(), search)
                prompt = tabs.settigns_tab.key_showhide.findChild(self.QtWidgets.QLineEdit)
                self.assertEqual(prompt.placeholderText(),
                                 "Press shortcut" if language == "en" else "按下快捷键")
                editor = tabs.override_tab.overlay_widget
                desktop_headers = [w.text() for w in editor.findChildren(self.QtWidgets.QLabel)]
                self.assertIn("Country" if language == "en" else "国家/地区", desktop_headers)
                self.assertIn("Games" if language == "en" else "对局数", desktop_headers)
                overlay_headers = [w.text() for w in tabs.settigns_tab.overlay_widget.findChildren(self.QtWidgets.QLabel)]
                self.assertIn("Country", overlay_headers)
                self.assertIn("Winrate", overlay_headers)
                self.assertEqual(tabs.settigns_tab.overlay_widget.civ_stats_label.textlabel, "CIV STATS")
                self.assertEqual(editor.players[0].flag.itemText(3), "English")
                self.assertEqual(editor.map.text(), "Map")
                self.assertEqual(tabs.random_tab.civ_label.text(), tabs.random_tab.current_civ)
                self.assertEqual(tabs.random_tab.map_label.text(), tabs.random_tab.current_map)
                self.assertFalse(tabs.random_tab.civ_image.pixmap().isNull())
                self.assertFalse(tabs.random_tab.map_image.pixmap().isNull())
                output = os.environ.get("AOE4_QA_OUTPUT")
                if output:
                    for index in range(tabs.count()):
                        tabs.setCurrentIndex(index)
                        self.app.processEvents()
                        window.grab().save(str(Path(output) / (language + "-" + str(index) + ".png")))

    def test_status_messages_and_user_values(self):
        self.settings.player_name = "玩家原文"
        self.settings.profile_id = 42
        self.settings.steam_id = 123
        self.settings.buildorders = {"自定义 Build Order": "English @unit_worker/villager@\n原文"}
        original = copy.deepcopy(self.settings.buildorders)
        tabs = self.window("zh_CN").centralWidget()
        page = tabs.settigns_tab
        page.update_profile_info()
        self.assertIn("玩家原文", page.profile_info.text())
        self.assertIn("玩家 ID：42", page.profile_info.text())
        page.aoe4net_error_msg()
        self.assertIn("服务出现问题", page.msg.text())
        self.assertIn("https://aoe4world.com/players/42", page.msg.text())
        with patch("overlay.tab_settings.scheldule") as schedule:
            page.multi_search.setText("玩家原文")
            page.find_profile()
            self.assertEqual(schedule.call_args.args[2], "玩家原文")
        with patch("overlay.tab_settings.keyboard.add_hotkey", side_effect=ValueError), \
                self.assertLogs("overlay.tab_settings", level="ERROR"):
            page.hotkey_changed("ctrl+b")
        self.assertEqual(page.msg.text(), "无法使用此快捷键")
        self.assertEqual(self.settings.buildorders, original)
        self.assertEqual(tabs.build_order_tab.bo_list.currentItem().text(), "自定义 Build Order")
        self.assertEqual(tabs.build_order_tab.bo_edit.toPlainText(), original["自定义 Build Order"])
        notes = tabs.build_order_tab.overlay.build_order_notes.labels
        self.assertEqual(notes[-1][0].text(), original["自定义 Build Order"])

    def test_history_business_values_and_override_payload_stay_original(self):
        from overlay.tab_games import MatchEntry
        self.settings.profile_id = 42
        tabs = self.window("zh_CN").centralWidget()
        history = {"game_id": 123, "map": "Dry Arabia", "kind": "qm_1v1",
                   "started_at": "2026-10-12T01:00:00.000Z", "teams": [
                       [{"player": {"profile_id": 42, "civilization": "english", "name": "玩家",
                                     "result": "win", "rating_diff": 12}}],
                       [{"player": {"profile_id": 43, "civilization": "french", "name": "Opponent"}}]]}
        entry = MatchEntry(tabs.games_tab.scroll_layout, history)
        self.assertEqual([w.text() for w in entry.widgets[2:7]],
                         ["Dry Arabia", "Oct 12, 01:00:00", "qm_1v1", "Win", "12"])
        self.assertIn("对局链接", entry.widgets[-1].text())
        editor = tabs.override_tab.overlay_widget
        editor.map.setText("Custom map 原文")
        editor.players[0].name.setText("玩家原文")
        editor.players[0].flag.setCurrentText("French")
        payload = editor.get_data()
        self.assertEqual(payload["map"], "Custom map 原文")
        self.assertEqual(payload["players"][0]["civ"], "French")
        self.assertEqual(payload["players"][0]["name"], "玩家原文")


if __name__ == "__main__":
    unittest.main()
