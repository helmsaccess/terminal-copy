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
