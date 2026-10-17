# Security

For a suspected vulnerability, use the repository's private security advisory reporting when enabled. Do not place private documents, credentials or exploit details containing sensitive data in a public issue.

The plugin renders Markdown locally. DOMPurify sanitizes document HTML, the page uses a Content Security Policy without inline script permission, and document scripts are not intentionally executed. Remote images may make requests, and explicitly clicked HTTP(S) links open in the system browser. Local state and a browser profile are stored under Sublime's cache. Closing a preview overwrites its state with a closed marker; the browser profile persists until its cache is removed.

Native integration is not a sandbox for hostile local programs. Any process running as the same user may be able to access the local cache. Review untrusted documents and keep WebView2 updated.

Diagnostics are disabled by default. Maintainer integration tests may explicitly enable browser evaluation/capture. Avoid enabling diagnostics for ordinary use.

Only the latest released experimental version is maintained. Dependency checks are a point-in-time check, not a guarantee that no vulnerability exists.
