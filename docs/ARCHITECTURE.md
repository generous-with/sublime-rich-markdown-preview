# Architecture

1. A Sublime Python plugin creates a read-only scratch tab in the current window. It preserves the original view/buffer and writes debounced document state to a unique per-session cache directory.
2. A separate C# helper creates a native `WS_CHILD` control with the Sublime HWND as its parent. It initializes WebView2 under that control. No additional top-level preview window is required.
3. Pane coordinates are converted using the parent window's DPI. Active-tab visibility and parent/plugin lifetime are monitored. Each session has its own state path so a rapid close/reopen cannot revive an old helper.
4. The browser loads bundled local assets. markdown-it parses Markdown; DOMPurify sanitizes HTML; highlight.js and Mermaid render code and diagrams.
5. Closing a preview writes a closed marker. The host closes its WebView2 controller and exits. Plugin reloads close active sessions; stale scheduler callbacks are rejected by an epoch token.

The helper is necessary because Sublime's minihtml is a limited renderer and does not provide ordinary selectable browser text. HWND embedding is a Windows integration technique, not an official embedded-browser API from Sublime.

Primary references: [Sublime API](https://www.sublimetext.com/docs/api_reference.html), [WebView2 controller](https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/win32/icorewebview2controller), [minihtml](https://www.sublimetext.com/docs/minihtml.html).
