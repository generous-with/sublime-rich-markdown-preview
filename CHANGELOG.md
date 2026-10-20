# Changelog

## 0.2.1 — prevent Package Control cleanup of manual installations

- Rename the plugin's version file to `rich-markdown-version.json`. The reserved `package-metadata.json` name incorrectly made a manual install look managed by Package Control, whose orphan cleanup could delete it because it was absent from `installed_packages`.
- Add a release-layout regression check. The fix keeps Package Control settings and User keybindings unchanged. Existing installations should upgrade using the installer so the old managed-package marker is removed.

## 0.2.0 — public experimental release

- Current-window WebView2 preview with native selection/copy and live unsaved updates.
- Standard Markdown formatting, local images, code highlighting, task lists and Mermaid.
- Refreshed pinned dependencies, retained notices, stricter script CSP and disabled-by-default diagnostics.
- General installation/uninstallation without changing User keybindings; portable path support and previous-version backup.
- Unique session state paths and stale-callback protection for close/reopen and plugin reloads.
- No personal paths, browser profiles, configuration backups or private screenshots in the source tree.
