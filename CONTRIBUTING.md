# Contributing

Bug reports and focused pull requests are welcome. Include Windows, Sublime build, WebView2 Runtime and display scaling versions, plus a minimal Markdown sample without private content.

Build and test using the README. Keep changes to the native host, renderer and Python lifecycle easy to review. Preserve the original window and source buffer; never close unrelated tabs by their names. Test copy/selection, unsaved updates, pane resizing, hidden tabs and close/reopen behavior for native UI changes.

Do not commit browser profiles, source document state, local paths, screenshots with private sidebars, installers, build output or personal configuration. Changes to dependencies must update integrity values and notices and rerun renderer tests. Do not report local tests as GitHub CI or broad platform acceptance.

Contributions are accepted under the project's MIT license. Third-party code requires its source and applicable license to be retained.
