# CitrusDrop — AI Agent Guidelines & Project Instructions

## Project Overview
- **Project**: CitrusDrop
- **Purpose**: Original, local-first Ubuntu desktop file converter and file action utility inspired by Tangerine's general workflow.
- **Stack**: Python 3.12, PySide6 (Qt Widgets), Pillow, FFmpeg CLI. Add other dependencies only when needed.
- **Platform**: Ubuntu 24.04 LTS with GNOME on Wayland (`$XDG_SESSION_TYPE == wayland`).

## Core Principles & Rules
1. **Local-First & Privacy**: All file processing is strictly local. Never introduce telemetry, analytics, tracking, or cloud upload services.
2. **Safe Output Handling**: Always preserve original files. Never silently overwrite existing outputs; use collision-avoidance suffixes (e.g., `_1`, `_2`) and pass `-n` to FFmpeg.
3. **Modular Architecture**: Keep UI (`main.py`), conversion logic (`converter.py`), and background workers strictly separated. Conversion logic must have zero Qt dependencies to remain independently testable.
4. **Responsive UI**: Run all file conversion and media processing in background worker threads (`QThread`). Never block the Qt main thread.
5. **Secure Process Execution**: Invoke external executables (e.g., FFmpeg) using argument lists via `subprocess.run()`. Never use `shell=True`.
6. **Wayland Compliance**: Respect Wayland's security model. Do not attempt global desktop input grabbing or uncoordinated window placement; document desktop integration limitations honestly.
7. **Verification & Testing**:
   - Write unit/integration tests for any non-trivial logic under `tests/`.
   - Run relevant tests and syntax checks after changes.
   - Never claim features, formats, or test results that have not been physically verified.
8. **Development Workflow**:
   - Implement one narrowly scoped task per prompt.
   - Inspect existing files before editing; review `git diff` afterwards.
   - Update `docs/current-status.md` and `docs/feature-roadmap.md` whenever milestone or architecture status changes.
