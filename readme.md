# Terminal Copy

Terminal Copy is an NVDA add-on for copying regions from Windows Terminal with the review cursor.

## Requirements

Terminal Copy version 0.1 requires NVDA 2026.1 or later and the Windows Terminal application.

The add-on interface and installed help are available in English and German.

## Installation

Open the `.nvda-addon` file, confirm the installation in NVDA, and restart NVDA when prompted.

## Copy a region

1. In Windows Terminal, move the NVDA review cursor to the first character and press `NVDA+R`.
2. Move to the last character and press `NVDA+R` again.
3. Press `NVDA+C` to copy the region, including both marked characters.

Press `NVDA+R` a third time to clear both marks. Marks may be set in either order, but must belong to
the same Windows Terminal buffer. NVDA announces each mark and whether copying succeeded.

The commands appear in NVDA's Input Gestures dialog under the `Terminal Copy` category and can be
remapped there.

## Scrollback and limitations

Terminal Copy uses Windows Terminal's UI Automation text ranges exposed through NVDA. This allows it
to copy available scrollback outside the visible viewport when the review cursor can reach it. Text
which Windows Terminal has already discarded from its buffer cannot be copied.

Lines containing only spaces or other whitespace inside the selected text are copied as empty lines.
Whitespace-only lines at the beginning or end are omitted. Trailing whitespace is removed from every
line, while leading indentation on lines containing visible text is preserved.

The two-mark interaction is inspired by
[Terminal Access for NVDA](https://github.com/PratikP1/Terminal-Access-for-NVDA) by Pratik Patel and is
adapted here for Terminal Copy's focused copying workflow.

## License

Terminal Copy is licensed under the GNU General Public License, version 2 or later.
