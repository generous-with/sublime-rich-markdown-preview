"""Regression tests for session ownership; no Sublime installation required."""
import importlib.util
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT = pathlib.Path(__file__).resolve().parents[1]


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        (ROOT / 'build').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(self.temp.cleanup)
        self.settings = {'asset_root': str(ROOT), 'runtime_root': self.temp.name}
        sublime = types.ModuleType('sublime')
        sublime.load_settings = lambda _: self.settings
        sublime.Region = lambda a, b: (a, b)
        sublime.platform = lambda: 'windows'
        sublime.set_timeout = Mock()
        sublime.set_timeout_async = Mock()
        plugin = types.ModuleType('sublime_plugin')
        plugin.TextCommand = plugin.WindowCommand = plugin.EventListener = object
        self.modules = patch.dict(sys.modules, sublime=sublime, sublime_plugin=plugin)
        self.modules.start()
        self.addCleanup(self.modules.stop)
        spec = importlib.util.spec_from_file_location('preview_under_test', ROOT / 'package/rich_markdown.py')
        self.app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.app)
        self.sublime = sublime
        self.window = Mock()
        self.window.id.return_value = 7
        self.window.hwnd.return_value = 42
        self.source, self.preview = Mock(), Mock()
        self.source.is_valid.return_value = self.preview.is_valid.return_value = True
        self.source.settings.return_value = Mock()
        self.preview.settings.return_value = Mock()
        self.window.get_view_index.return_value = (1, 0)
        self.window.active_view_in_group.return_value = self.preview
        self.preview.layout_to_window.return_value = (100, 30)
        self.preview.viewport_extent.return_value = (600, 700)
        self.source.substr.return_value = '# Unsaved private text'
        self.source.file_name.return_value = str(ROOT / 'examples/sample.md')
        self.startup = patch.object(self.app.subprocess, 'STARTUPINFO', create=True)
        self.startup.start()
        self.addCleanup(self.startup.stop)
        for name in ('STARTF_USESHOWWINDOW', 'CREATE_NO_WINDOW'):
            p = patch.object(self.app.subprocess, name, 0, create=True)
            p.start()
            self.addCleanup(p.stop)

    def start(self):
        return self.app.start_session(self.window, self.source, self.preview, {}, False)

    @patch('subprocess.Popen')
    def test_reopening_uses_distinct_state_files_and_clears_old_document(self, popen):
        first = self.start()
        self.app.stop_session(7)
        second = self.start()
        self.assertNotEqual(first['state_path'], second['state_path'])
        self.assertEqual(pathlib.Path(first['state_path']).read_text(), '{"closed": true}')
        self.assertIn('Unsaved private text', pathlib.Path(second['state_path']).read_text())

    @patch('subprocess.Popen')
    def test_close_reopen_does_not_share_a_browser_profile(self, popen):
        self.start()
        old_profile = popen.call_args.args[0][4]
        self.app.stop_session(7)
        self.start()
        new_profile = popen.call_args.args[0][4]
        self.assertNotEqual(old_profile, new_profile,
                            'A new helper must not wait on the previous WebView2 profile')

    @patch('subprocess.Popen')
    def test_profile_cleanup_waits_for_helper_exit(self, popen):
        session = self.start()
        profile = pathlib.Path(popen.call_args.args[0][4])
        profile.mkdir()
        (profile / 'cache.txt').write_text('temporary browser data')
        session['process'].poll.return_value = None
        self.app.cleanup_profile(session)
        self.assertTrue(profile.exists())
        self.sublime.set_timeout_async.assert_called_once()
        session['process'].poll.return_value = 0
        self.app.cleanup_profile(session)
        self.assertFalse(profile.exists())
        self.assertTrue(pathlib.Path(session['state_path']).exists())

    def test_profile_cleanup_rejects_paths_outside_its_cache(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build') as other:
            profile = pathlib.Path(other) / 'browser-profile'
            profile.mkdir()
            self.app.cleanup_profile({'state_path': str(pathlib.Path(other) / 'state.json')})
            self.assertTrue(profile.exists())

    @patch('subprocess.Popen')
    def test_failed_host_does_not_cover_its_error_message(self, popen):
        self.source.window.return_value = self.window
        session = self.start()
        session['process'].poll.return_value = 1
        self.app.running = True
        self.app.tick(self.app.epoch)
        self.assertTrue(session['overlay'])
        self.preview.run_command.assert_called_once()
        self.app.tick(self.app.epoch)
        import json
        payload = json.loads(pathlib.Path(session['state_path']).read_text())
        self.assertFalse(payload['visible'])

    @patch('subprocess.Popen')
    def test_browser_evaluation_requires_explicit_diagnostics_opt_in(self, popen):
        self.start()
        self.assertNotIn('--diagnostics', popen.call_args.args[0])
        self.app.stop_session(7)
        self.settings['enable_diagnostics'] = True
        self.start()
        self.assertEqual(popen.call_args.args[0][-1], '--diagnostics')

    @patch('subprocess.Popen', side_effect=OSError('missing executable'))
    def test_failed_launch_releases_session_and_source_marker(self, popen):
        with self.assertRaisesRegex(OSError, 'missing executable'):
            self.start()
        self.assertEqual(self.app.sessions, {})
        self.source.settings().erase.assert_called_with(self.app.SOURCE_KEY)
        state = next(pathlib.Path(self.temp.name).glob('*/state.json'))
        self.assertEqual(state.read_text(), '{"closed": true}')

    def test_old_reload_timer_cannot_restart_polling(self):
        self.app.running = True
        self.app.tick(object())
        self.sublime.set_timeout.assert_not_called()
        self.app.tick(self.app.epoch)
        self.sublime.set_timeout.assert_called_once()

    def test_other_platform_does_not_start_native_loop(self):
        self.sublime.platform = lambda: 'linux'
        self.app.plugin_loaded()
        self.sublime.set_timeout.assert_not_called()


if __name__ == '__main__':
    unittest.main()
