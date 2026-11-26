# Windows Terminal AppModule interoperability

Terminal Copy avoids the shared `appModules.windowsterminal` name because NVDA can load only one
module with that name. A minimal global plugin maps the `windowsterminal` executable to Terminal
Copy's uniquely named `appModules.terminalCopyWindowsterminal` module. Commands, UIA access, state,
and application lifecycle remain in that AppModule.

The uniquely named module imports a direct `appModules.windowsterminal.AppModule` as its base when
another add-on supplies one. Otherwise it derives from `appModuleHandler.AppModule`, retaining
NVDA's native UIA terminal objects. Only absence of the direct module activates the fallback; an
import failure inside a companion module remains visible.

Both lifecycle methods call `super`, so a companion module retains its scripts, events, overlay
selection, initialization, and cleanup. Terminal Copy registers its mapping during global-plugin
initialization and removes it during termination, including Plugin Reload.

NVDA exposes only one add-on alias for each executable. This design composes with a direct
`windowsterminal` AppModule, but it cannot generally compose with another add-on which also registers
an executable alias for `windowsterminal`.

Regression tests cover standalone fallback, registration and reload, companion inheritance,
Terminal Copy copying while composed, companion scripts, events, overlays and lifecycle, visible
companion import failures, and the exact packaged module layout. Manual validation for version 0.1.1
confirmed combined operation with NVDA, Windows Terminal, and Neovim Access Link.

## Classic Windows Command Prompt

The global plugin also maps `cmd` and `conhost` to
`appModules.terminalCopyConsole`. The commands use NVDA's current review range
when its owner is the focused `ConsoleWindowClass` object. The two AppModules
share the mark, range construction and clipboard logic.

UI Automation ranges keep their provider and are read in a COM worker. NVDA's
legacy `WinConsoleTextInfo` uses a handle shared by whichever legacy console
has focus and stores viewport-relative offsets. Terminal Copy verifies the
focused object and the captured viewport before constructing or reading a
legacy range. It captures NVDA's formatted clipboard text synchronously and
passes the string to the worker for normalization and clipboard output. Keep
these NVDA-specific details within the classic console AppModule.
[NVDA Console UIA implementation](https://github.com/nvaccess/nvda/blob/release-2026.3.1/source/NVDAObjects/UIA/winConsoleUIA.py) ·
[NVDA legacy console implementation](https://github.com/nvaccess/nvda/blob/release-2026.3.1/source/winConsoleHandler.py)
