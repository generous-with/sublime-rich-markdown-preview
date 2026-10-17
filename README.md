# Rich Markdown Preview for Sublime Text

[简体中文](README.zh-CN.md) · [MIT license](LICENSE)

Render Markdown in the **current Sublime Text window** with a real WebView2 browser, live unsaved updates, and native text selection/copy.

**Experimental — Windows x64 only.** This is a custom plugin with a native helper, not an official Sublime browser component. macOS and Linux are not supported.

![Actual embedded browser rendering of the included sample](docs/preview.png)

## Features

- Preview in an adjacent editor group; keep the original document and buffer open.
- Real HTML formatting: headings, emphasis, tables, images, syntax-highlighted code and task lists.
- Mermaid diagrams rendered locally.
- Select preview text and copy with Ctrl+C or the browser context menu.
- Live updates without saving; preview follows pane size and hides on other tabs.
- Supports unsaved/unnamed documents. Closing the preview stops its helper process.

## Requirements

- Windows 10/11 x64 and Sublime Text 4 with the Windows `Window.hwnd()` API (build 4144+).
- Microsoft Edge WebView2 Evergreen Runtime and .NET Framework 4.8.
- The native integration was tested on build 4215 at 200% DPI. Older builds and other DPI/display configurations still need community testing.

## Install a release

1. Download and unzip the Windows archive from [Releases](https://github.com/generous-with/sublime-rich-markdown-preview/releases).
2. Close any existing Rich Markdown previews.
3. From the extracted folder, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\install.ps1
```

If multiple Sublime data directories exist, or you use a portable installation, specify the **Packages** directory shown by **Preferences > Browse Packages**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\install.ps1 -PackagesPath "X:\YourSublimeData\Packages"
```

The installer backs up an existing package before replacing it. It does not modify your User settings or keybindings. You can also manually copy the extracted `RichMarkdownPreview` folder into Sublime's Packages folder.

This package must remain an **unpacked folder**: its native helper cannot run from inside a `.sublime-package` archive. It is not currently available through Package Control. The release executable is unsigned; source builds are available below.

## Use

Open a Markdown document and press **Alt+M**, or choose **Rich Markdown: Preview in Current Window** in the command palette.

The default shortcut is scoped to Markdown. If your User keymap already binds Alt+M, use the command palette or add your own binding:

```json
{"keys":["alt+m"],"command":"rich_markdown_preview","context":[{"key":"selector","operand":"text.html.markdown"}]}
```

Close the preview tab, or use **Rich Markdown: Close Preview**. While the embedded browser has keyboard focus, browser shortcuts apply; click the source editor to use Sublime editing shortcuts.

To uninstall after closing previews:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\uninstall.ps1
```

Use the same `-PackagesPath` argument if it was needed for installation. User documents and User settings are retained.

## Build and test

With Python 3.8+ and the existing .NET Framework compiler on Windows:

```powershell
python tools\fetch_dependencies.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools\build-host.ps1
python -m unittest discover -s tests -p "test_*.py"
powershell -NoProfile -ExecutionPolicy Bypass -File tools\package.ps1
```

Pinned dependency archives are verified against `dependencies.lock.json` before extraction. Downloaded dependencies, browser profiles, build output and local test artifacts are excluded from Git. Release archives include the required runtime assets and licenses, so rendering does not require a CDN connection.

Browser tests:

```powershell
npm install --ignore-scripts
npx playwright install chromium
npm test
```

See [validation](docs/VALIDATION.md), [architecture](docs/ARCHITECTURE.md), [contributing](CONTRIBUTING.md), and [security](SECURITY.md).

## Limitations

- No math formula extension or relative file-link navigation yet. Images work; remote images can make network requests.
- Rendering follows markdown-it, not another editor's theme or extension set. Pixel-identical output is not promised.
- Native child-window integration needs retesting after Sublime, Windows or WebView2 updates. Package reloads close active previews.
- Screen readers, multi-monitor DPI changes, IME behavior and large-document performance have not been comprehensively validated.

Original integration code is MIT-licensed. Dependencies retain their own licenses; see [third-party notices](THIRD_PARTY_NOTICES.md).
