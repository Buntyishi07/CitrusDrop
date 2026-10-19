# CitrusDrop — Wayland Compatibility

## Session Type

CitrusDrop targets **Ubuntu 24.04 with GNOME on Wayland** (`$XDG_SESSION_TYPE == wayland`).

PySide6 applications run on Wayland via the `wayland` Qt platform plugin (default on GNOME Wayland sessions). The `xcb` plugin is also available as a fallback for X11 or XWayland.

## What Works

### In-app drag-and-drop ✅
Qt's internal drag-and-drop mechanism works correctly on Wayland. Files can be dragged from:
- **Nautilus** (the GNOME file manager) into the CitrusDrop drop zone
- Other applications that implement standard Wayland DnD

The `DropZone` widget uses `QFrame.setAcceptDrops(True)`, `dragEnterEvent`, `dragLeaveEvent`, and `dropEvent` — all standard Qt DnD APIs that work on Wayland.

### Modal dialogs ✅
The radial picker uses `QDialog` with `exec()`. Modal dialogs work correctly on Wayland.

### File dialogs ✅
`QFileDialog.getOpenFileNames()` uses the XDG Desktop Portal on GNOME Wayland by default (via `QGtk3Theme` or the portal integration), providing a native-looking file chooser.

### Window management basics ✅
`QMainWindow`, `resize`, `setMinimumSize`, `show` all work correctly.

### Clipboard ✅
Qt's clipboard API (`QClipboard`) works on Wayland for copy/paste operations within the application and between applications.

## What Does Not Work

### Global drag interception ❌
**Tangerine's signature interaction — intercepting any drag anywhere on the desktop and showing a radial menu — is not possible on Wayland.**

Wayland's security model does not allow applications to:
- Intercept input events destined for other windows
- Overlay arbitrary windows above all other applications without compositor cooperation
- Monitor mouse/keyboard events globally

On X11, this was possible via `XGrabPointer`, `XQueryPointer`, and always-on-top windows. Wayland deliberately removed these capabilities for security.

**Mitigation**: CitrusDrop provides an in-app drag-and-drop workflow. Files are dragged into the application window, where the radial menu and conversion options are available.

### Global keyboard shortcuts ❌
Registering system-wide keyboard shortcuts (like "press a hotkey to open CitrusDrop") requires:
- GNOME's keyboard shortcut settings (manual user setup)
- Or `org.freedesktop.portal.GlobalShortcuts` (available in Portal v4+, support varies)

**Mitigation**: Users can set up a custom shortcut in GNOME Settings to launch CitrusDrop.

### Frameless overlay windows (limited) ⚠️
The radial picker uses `Qt.WindowType.FramelessWindowHint` and `WA_TranslucentBackground`. On Wayland:
- Frameless windows work but cannot be positioned at arbitrary screen coordinates
- Windows cannot be placed above all other windows without compositor support
- `setWindowFlags(Qt.WindowStaysOnTopHint)` may not work reliably

**Mitigation**: The radial picker is shown as a modal dialog centered on the main window, not as a free-floating overlay.

### Window positioning ⚠️
On Wayland, `QWidget.move()` and `QWidget.setGeometry()` do not reliably position top-level windows. The compositor controls window placement.

**Mitigation**: Use layouts and relative positioning within the application window. Do not depend on absolute screen coordinates.

## Future Desktop Integration Options

### XDG Desktop Portal
The [XDG Desktop Portal](https://flatpak.github.io/xdg-desktop-portal/) provides a D-Bus API for:
- `org.freedesktop.portal.FileChooser` — file selection ✅ (already used by Qt)
- `org.freedesktop.portal.Notification` — system notifications
- `org.freedesktop.portal.GlobalShortcuts` — hotkey registration (Portal v4+)
- `org.freedesktop.portal.Background` — background running permission

### Nautilus Scripts / Actions
GNOME's Nautilus file manager supports:
- **Scripts**: `~/.local/share/nautilus/scripts/` — shell scripts accessible via right-click
- **nautilus-python extension**: Python scripts that add menu items to Nautilus

This could allow "Convert with CitrusDrop" in the Nautilus right-click menu.

### `.desktop` File
A standard `.desktop` file in `~/.local/share/applications/` enables:
- Launcher icon in GNOME Activities
- File association (open specific file types with CitrusDrop)
- Custom MIME type handling

### D-Bus Activation
CitrusDrop could expose a D-Bus service that Nautilus scripts or other tools call to queue files for conversion.

## Recommendations

1. **Do not claim global drag interception works.** It does not on Wayland, and pretending otherwise would be dishonest.
2. **Build a great in-app experience first.** Make the drop zone obvious, the radial menu fast, and the workflow smooth.
3. **Investigate Nautilus integration early.** Right-click "Convert with CitrusDrop" is the closest achievable equivalent to Tangerine's drag-anywhere model.
4. **Monitor Portal API evolution.** `GlobalShortcuts` and compositor-level overlays may become more capable.
5. **Test on both Wayland and X11.** Some users still run X11 sessions; the app should work on both.

## Testing Wayland Compatibility

```bash
# Check session type
echo "$XDG_SESSION_TYPE"   # should print "wayland"

# Check Qt platform
QT_DEBUG_PLUGINS=1 python main.py 2>&1 | grep -i "platform"

# Force Wayland backend (if not default)
QT_QPA_PLATFORM=wayland python main.py

# Force X11 backend (fallback testing)
QT_QPA_PLATFORM=xcb python main.py
```
