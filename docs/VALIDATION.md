# Validation scope

The initial local prototype was exercised on Windows x64, Sublime build 4215, Python 3.14, WebView2 Runtime 155.0.4283.60 and 200% DPI. Its 27 checks covered native parent ownership, preserved window/source buffer, formatting, images, Mermaid, selection/copy, unsaved updates, pane resizing, tab visibility, unnamed buffers and helper exit/reopen.

That prototype evidence is not a claim that every later revision, display configuration or Sublime version passed the same checks. Personal paths, profiles and raw local logs are excluded from this repository.

For the public preparation, dependencies were refreshed, browser tests were rerun, and installer/lifecycle tests are maintained under `tests/`. Automated GitHub CI results apply only after the relevant workflow actually runs. Headless renderer tests validate HTML behavior; they do not prove native Sublime window embedding.

On 2026-10-18, public version 0.2.0 was also exercised in a dedicated Sublime window with an isolated command namespace. All 13 embedding/rendering checks and 14 interaction checks passed again, including real clipboard copy, unsaved changes and helper close/reopen. See the sanitized [local result](validation-local.json). The public renderer and C# host were used; the currently installed user plugin was not replaced by the test.

The five Python lifecycle regressions and PowerShell installer checks passed locally. Installer checks cover a fresh install, upgrade backup, preservation of User keybindings, checksum rejection, target-path rejection and uninstall in a workspace fixture.

Manual acceptance still matters for keyboard focus, IME, accessibility, mixed-DPI monitors and a user's own document/extension expectations.
