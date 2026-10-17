"""Windows Markdown preview using an actual embedded WebView2 child window."""
import json
import os
import pathlib
import subprocess
import time
import uuid
import sublime
import sublime_plugin

sessions = {}
PREVIEW_KEY = 'rich_markdown_webview'
SOURCE_KEY = 'rich_markdown_source'
SINGLE = {'cols': [0.0, 1.0], 'rows': [0.0, 1.0], 'cells': [[0, 0, 1, 1]]}
DOUBLE = {'cols': [0.0, 0.5, 1.0], 'rows': [0.0, 1.0], 'cells': [[0, 0, 1, 1], [1, 0, 2, 1]]}
running = False
epoch = object()


def asset_root():
    return sublime.load_settings('RichMarkdownPreview.sublime-settings').get('asset_root') or os.path.dirname(__file__)


def runtime_root():
    return sublime.load_settings('RichMarkdownPreview.sublime-settings').get('runtime_root') or os.path.join(sublime.cache_path(), 'RichMarkdownPreview')


def atomic_json(path, value):
    temporary = path + '.tmp'
    with open(temporary, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False)
    os.replace(temporary, path)


def start_session(window, source, preview, layout, owns_layout):
    root = asset_root()
    directory = os.path.join(runtime_root(), '{}-{}-{}'.format(os.getpid(), window.id(), uuid.uuid4().hex[:12]))
    os.makedirs(directory, exist_ok=True)
    state_path = os.path.join(directory, 'state.json')
    session = {'source': source, 'preview': preview, 'original_layout': layout, 'owns_layout': owns_layout,
               'state_path': state_path, 'generation': 0, 'changed': 0, 'markdown': None,
               'snapshot': None, 'process': None, 'overlay': False, 'started': time.monotonic(), 'error_reported': False}
    source.settings().set(SOURCE_KEY, True)
    preview.settings().set(PREVIEW_KEY, True)
    preview.set_scratch(True)
    preview.set_read_only(True)
    preview.settings().set('line_numbers', False)
    preview.settings().set('gutter', False)
    preview.settings().set('word_wrap', False)
    sessions[window.id()] = session
    update_session(window, session, force=True)
    try:
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = 0
        arguments = [
            os.path.join(root, 'bin', 'PreviewHost.exe'), state_path, str(window.hwnd()),
            os.path.join(root, 'web', 'preview.html'), os.path.join(runtime_root(), 'profiles', str(window.id()))
        ]
        if sublime.load_settings('RichMarkdownPreview.sublime-settings').get('enable_diagnostics', False):
            arguments.append('--diagnostics')
        session['process'] = subprocess.Popen(arguments, startupinfo=info, creationflags=subprocess.CREATE_NO_WINDOW,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        stop_session(window.id())
        raise
    return session


def update_session(window, session, force=False):
    source, preview = session['source'], session['preview']
    if not source.is_valid() or not preview.is_valid() or not window.is_valid():
        return
    group = window.get_view_index(preview)[0]
    active = window.active_view_in_group(group)
    origin = preview.layout_to_window(preview.viewport_position())
    extent = preview.viewport_extent()
    visible = bool(active and active.id() == preview.id() and not session['overlay'])
    now = time.monotonic()
    if force or (now - session['changed'] >= .16):
        text = source.substr(sublime.Region(0, source.size()))
        if text != session['markdown']:
            session['markdown'] = text
            session['generation'] += 1
    folder = os.path.dirname(source.file_name()) if source.file_name() else (window.folders() or [os.getcwd()])[0]
    payload = {'rect': {'x': origin[0], 'y': origin[1], 'width': extent[0], 'height': extent[1]},
               'visible': visible, 'generation': session['generation'], 'markdown': session['markdown'] or '',
               'owner_pid': os.getpid(),
               'base_uri': pathlib.Path(folder).as_uri().rstrip('/') + '/'}
    for key in ('evaluate', 'capture'):
        if key in session:
            payload[key] = session[key]
    if force or payload != session['snapshot']:
        atomic_json(session['state_path'], payload)
        session['snapshot'] = payload


def tick(token):
    if not running or token is not epoch:
        return
    for window_id, session in list(sessions.items()):
        source, preview = session['source'], session['preview']
        window = source.window() if source.is_valid() else None
        if not window or not preview.is_valid():
            stop_session(window_id)
            continue
        try:
            update_session(window, session)
            process = session['process']
            if process and not session['error_reported']:
                message = None
                if process.poll() is not None:
                    message = 'Preview host exited. Close this tab and retry; check the WebView2 Runtime installation.'
                else:
                    status_path = session['state_path'] + '.status.json'
                    try:
                        with open(status_path, encoding='utf-8') as stream:
                            status = json.load(stream)
                        if status.get('error'):
                            message = 'WebView2 could not initialize. Check View > Show Console for details.'
                            print('RichMarkdownPreview:', status['error'])
                    except (OSError, ValueError):
                        if time.monotonic() - session['started'] > 30:
                            message = 'Preview startup timed out. Close this tab and retry.'
                if message:
                    session['error_reported'] = True
                    preview.run_command('rich_markdown_message', {'text': message})
        except (OSError, RuntimeError) as error:
            print('RichMarkdownPreview:', error)
    sublime.set_timeout(lambda: tick(token), 120)


def stop_session(window_id):
    session = sessions.pop(window_id, None)
    if not session:
        return
    try:
        atomic_json(session['state_path'], {'closed': True})
    except OSError:
        pass
    if session['source'].is_valid():
        session['source'].settings().erase(SOURCE_KEY)
    if session['preview'].is_valid():
        session['preview'].settings().erase(PREVIEW_KEY)
    return session


def plugin_loaded():
    global running
    running = True
    if sublime.platform() == 'windows':
        token = epoch
        sublime.set_timeout(lambda: tick(token), 120)


def plugin_unloaded():
    global running
    running = False
    for window_id in list(sessions):
        stop_session(window_id)


class RichMarkdownPreviewCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return sublime.platform() == 'windows' and not self.view.settings().get(PREVIEW_KEY) and self.view.match_selector(0, 'text.html.markdown')

    def run(self, edit):
        source, window = self.view, self.view.window()
        if not window:
            return
        current = sessions.get(window.id())
        if current and current['preview'].is_valid():
            current['overlay'] = False
            if current['source'].is_valid():
                current['source'].settings().erase(SOURCE_KEY)
            current['source'] = source
            source.settings().set(SOURCE_KEY, True)
            current['changed'] = 0
            preview = current['preview']
            group = window.get_view_index(source)[0]
            if window.get_view_index(preview)[0] == group:
                if window.num_groups() == 1:
                    window.set_layout(DOUBLE)
                window.set_view_index(preview, (group + 1) % window.num_groups(), -1)
            window.focus_view(preview)
            window.focus_view(source)
            update_session(window, current, force=True)
            return
        layout = window.get_layout()
        owns_layout = window.num_groups() == 1
        if owns_layout:
            window.set_layout(DOUBLE)
        group = (window.get_view_index(source)[0] + 1) % window.num_groups()
        window.focus_group(group)
        preview = window.new_file()
        preview.set_name('Markdown Preview')
        try:
            start_session(window, source, preview, layout, owns_layout)
        except Exception as error:
            preview.close()
            sublime.error_message('Markdown preview could not start: ' + str(error))
        window.focus_view(source)


class RichMarkdownCloseCommand(sublime_plugin.WindowCommand):
    def run(self):
        session = sessions.get(self.window.id())
        if session and session['preview'].is_valid():
            session['preview'].close()


class RichMarkdownMessageCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        if self.view.settings().get(PREVIEW_KEY):
            self.view.set_read_only(False)
            try:
                self.view.replace(edit, sublime.Region(0, self.view.size()), text)
            finally:
                self.view.set_read_only(True)


class RichMarkdownEvents(sublime_plugin.EventListener):
    def on_modified_async(self, view):
        def changed():
            window = view.window()
            session = sessions.get(window.id()) if window else None
            if session and session['source'].id() == view.id():
                session['changed'] = time.monotonic()
        sublime.set_timeout(changed, 0)

    def on_pre_close(self, view):
        window = view.window()
        session = sessions.get(window.id()) if window else None
        if not session or view.id() not in (session['source'].id(), session['preview'].id()):
            return
        closing_source = view.id() == session['source'].id()
        group = window.get_view_index(session['preview'])[0]
        stop_session(window.id())
        def finish():
            if closing_source and session['preview'].is_valid():
                session['preview'].close()
            if session['owns_layout'] and window.is_valid() and window.num_groups() == 2 and not window.sheets_in_group(group):
                window.set_layout(session['original_layout'])
        sublime.set_timeout(finish, 0)

    def on_pre_close_window(self, window):
        stop_session(window.id())

    def on_window_command(self, window, command, args):
        session = sessions.get(window.id())
        if session:
            session['overlay'] = command == 'show_overlay'
