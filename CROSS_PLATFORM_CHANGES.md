# Cross-Platform Changes

The project now supports Windows, macOS, and Linux while keeping the existing
game rules, timing settings, save formats, item formats, key names, mouse
coordinate convention, sound commands, and screen layouts unchanged.

The terminal must support UTF-8 and ANSI/VT escape sequences. The standard
modern terminals on all three operating-system families do.

## Change inventory

### `console_input.py`

- Split console input into OS-selected backends. Windows still uses Console
  Input Records, so its established key repeat, virtual-key, mouse, and timeout
  behavior is retained. The Win32 imports and structures are now loaded only on
  Windows, preventing import-time failures on macOS and Linux.
- Added a macOS/Linux backend using the standard-library `termios`, `tty`,
  `select`, and `os.read` APIs. It uses blocking polling rather than a busy loop
  and restores the terminal attributes after each call so the game's existing
  line-oriented `input()` screens continue to work.
- Decoded the same public key names used by the game: printable UTF-8
  characters, `space`, `enter`, `backspace`, `esc`, arrow directions, and
  `ctrl/<letter>`. The existing `key(timeout=None, mouse=False)` signature and
  `"TIMEOUT"` sentinel are unchanged.
- Added ANSI SGR mouse decoding on macOS/Linux for button down/up, left-button
  drag, wheel, and double-click events. SGR's one-based positions are converted
  to the zero-based coordinates already used by the Windows backend and the
  settings UI.
- Added exit cleanup for POSIX mouse-reporting modes so the terminal is restored
  even when the game exits while mouse input is enabled.

Why necessary: the previous module accessed `ctypes.windll.kernel32`
unconditionally and could not even be imported outside Windows.

Gameplay impact: none intended. Key strings, timeout behavior, and coordinate
shape are preserved. POSIX double-click detection uses a 500 ms interval because
terminal protocols do not provide the OS double-click classification that the
Windows console provides. A terminal with unusual escape sequences may have
different mouse behavior; keyboard navigation remains the exact fallback.
During validated text entry, arrow and other named special keys are now ignored
consistently. The former direct `msvcrt.getwch()` path could expose the second
byte of a Windows extended-key sequence as a printable character. Retaining a
conditional `msvcrt` text path is the alternative if that accidental scan-code
insertion behavior is required.

Performance impact: negligible. POSIX waits use `select`, so idle input consumes
no polling CPU. Saving/restoring terminal attributes adds a small system-call
cost per input call; this is bounded by the game's existing animation polling
rate. A third-party event library such as `curses`/`blessed` could instead keep a
persistent terminal session, but would add a dependency and require broader UI
changes.

### `main.py`

- Removed the unconditional `msvcrt` dependency. The validated text-entry
  helper now reads from the shared `key()` API and maps its `space`, `enter`, and
  `backspace` names back to the same text-editing actions.
- Replaced the Windows `title` shell command with the portable ANSI terminal
  title sequence. It is emitted only for an interactive terminal, avoiding
  control data in redirected output.
- Made Windows ANSI enablement conditional. macOS and Linux skip the Win32 API
  call because ANSI support is native there.
- Replaced Win32 cursor visibility calls with ANSI show/hide sequences.
- Replaced `os.system("cls")` with an ANSI clear-and-home sequence. This also
  removes a shell process from every clear operation.
- Anchored the process working directory to the directory containing `main.py`.
  Legacy relative save, item, settings, script, and asset paths therefore point
  to the same project files whether the game is launched from a shell, Finder,
  a desktop shortcut, or an absolute script path.
- Started `sound_player.py` with an absolute script path and the project root as
  its working directory.
- Added cross-platform normal-exit cleanup for the sound helper. Windows also
  retains forced-close cleanup through a correctly scoped Job Object assigned
  to the sound child; non-Windows systems use normal process termination and
  their shared terminal process lifecycle.
- Anchored menu-wipe subprocess launches to the project directory.
- Changed the sound command queue to the canonical
  `General/Temp/sound_cmd_queue.txt` path and creates its parent directory if
  needed. This fixes the prior lowercase `general/temp` lookup, which happened
  to work on case-insensitive Windows filesystems but failed on case-sensitive
  Linux filesystems.
- Corrected every other lowercase `general/...` runtime reference to the actual
  `General/...` directory spelling.
- Replaced the hard-coded `notepad.exe` inventory-item editor with a portable
  launcher. Windows still opens Notepad; macOS/Linux first honor `VISUAL` or
  `EDITOR`, macOS otherwise uses `open -W`, and Linux otherwise uses
  `xdg-open`, `nano`, or `vi` in that order of availability.
- Updated the settings mouse-coordinate comment to describe the now-common
  zero-based input contract rather than Win32 specifically.

Why necessary: the old startup, cursor, clear, input, child-process, path-casing,
and editor code either failed immediately or invoked missing Windows programs
on macOS/Linux.

Gameplay impact: none intended. All game state remains under the same project
folders and all control actions retain their names. Anchoring the working
directory can affect an undocumented workflow that deliberately launched the
game from another directory to use a second set of relative data files. A
future `--data-dir` option would be the safer explicit alternative for that
workflow.

The ANSI clear sequence clears the visible screen and homes the cursor, matching
the layout behavior used by the game. Some terminals retain cleared content in
scrollback whereas Windows `cls` may handle scrollback differently. If clearing
scrollback is required, `ESC[3J` can be added, but that is more destructive to a
user's terminal history and is not needed for gameplay.

Graphical Linux openers may return as soon as they hand the file to an editor,
whereas Notepad and `open -W` wait for the editor to close. Set `VISUAL` or
`EDITOR` to a command with its editor's wait flag (for example,
`EDITOR="code --wait"`) when identical waiting behavior is important. This
action is a developer convenience and does not affect combat or progression.

Performance impact: screen clears are slightly cheaper because no shell process
is created. Other changes occur only at startup, shutdown, sound queuing, or the
developer-only item editor and have no meaningful runtime cost.

### `wipe.py`

- Replaced Win32 cursor positioning and `WriteConsoleW` with ANSI cursor
  positioning and normal UTF-8 stream writes. A small guarded Windows setup
  enables VT output when the utility is run directly.
- Replaced the Windows-only `winsound.MessageBeep` optional notification with
  the portable ASCII BEL terminal notification.
- Renamed the command description from a Windows terminal engine to a generic
  terminal engine.

Why necessary: `ctypes.windll` and `winsound` prevented the transition helper
from importing or running on macOS/Linux.

Gameplay impact: none. The game invokes the same wipe modes with the same delay
values and does not use the optional `--sound` flag. BEL can be silent or visual
depending on terminal preferences; if a guaranteed audible standalone wipe
notification is required, the alternative is to use the existing pygame audio
layer at the cost of starting the mixer.

The standalone utility now respects standard-output redirection; the former
Windows handle writes always targeted the console. A Windows-only direct-handle
branch would preserve that redirection-bypassing behavior, but would undermine
the portable stream contract and is unnecessary for game transitions.

Performance impact: no meaningful change. Writes are flushed immediately, as
the former direct console writes were, so animation timing is preserved.

### `sound_player.py`

- The optional ffmpeg metadata-cleaning subprocess now receives
  `CREATE_NO_WINDOW` only on Windows. The `creationflags` keyword is omitted
  entirely on macOS/Linux.
- Replaced a backslash-only `Sounds\\Music` comment with the portable path
  spelling used by the implementation, and removed an obsolete reference to
  the Windows command shell from the file-queue description.

Why necessary: subprocess creation flags are platform-specific even though the
ffmpeg command itself is portable.

Gameplay impact: none. The ffmpeg arguments, metadata behavior, fallback, and
audio data are unchanged.

Performance impact: none.

### `sort.py`

- Resolved `Items/Weapons` from the script directory instead of the caller's
  current working directory.

Why necessary: launching the maintenance utility from another directory could
sort the wrong tree or fail, and GUI/shell launch working directories vary by
platform.

Gameplay impact: none; the sorter still applies the same ordering and renaming
logic to the project's weapon files. As with the main process, an undocumented
alternate-working-directory workflow would now need an explicit path option.

Performance impact: none.

### `readme.md` and `Docs/*.md`

- Documented Windows, macOS, and Linux support, plus the UTF-8/ANSI terminal
  requirement and the terminal-dependent nature of mouse reporting. Removed
  the obsolete documentation claim that a Windows console was required.

Gameplay and performance impact: none; documentation only.

## Behavior-sensitive alternatives summary

The changes do not alter combat, progression, persistence formats, randomness,
animation-delay settings, or audio mixing. The only environment-level
differences that may be observable are:

1. POSIX double clicks use a 500 ms terminal-side classification. Keyboard
   controls are the exact alternative when a terminal does not report mouse
   events reliably.
2. ANSI clear may preserve terminal scrollback. Adding `ESC[3J` would clear it,
   but was intentionally avoided.
3. Linux desktop openers may not wait for the editor. Configure `VISUAL` or
   `EDITOR` with a wait-capable command for strict waiting.
4. Relative data is now deliberately anchored to the project. An explicit
   `--data-dir` option would be preferable to relying on the launch directory
   for alternate profiles.
5. Terminal BEL respects the user's terminal notification settings. Pygame is
   the alternative for a guaranteed application-controlled sound.
6. Cross-platform `atexit` cleanup cannot run after an uncatchable hard kill.
   POSIX terminals normally signal the whole foreground process group, which
   also ends the sound helper. A parent-death watchdog would be the alternative
   if orphan prevention after `SIGKILL` must be guaranteed on Linux; macOS has
   no directly equivalent standard-library primitive.

## Verification performed

- Compiled every Python source file with `py_compile`.
- Ran the existing unittest suite: 25 tests passed. One unrelated data-state
  assertion fails because the already-modified `Items/Weapons/item15.txt` has
  refinement `3`, while `test_seed_weapons_start_unrefined` expects `0`.
- Exercised the portable input parser with printable text, UTF-8 text, Enter,
  Backspace, Space, Ctrl+R, all four arrow sequences, mouse down/up/drag, wheel,
  and zero-based coordinate conversion.
- Exercised the ANSI wipe renderer against a controlled terminal size.
- Verified that closing the guarded Windows Job Object terminates a managed
  child process.
- Re-scanned all Python sources for Windows-only imports/APIs, shell commands,
  drive-letter paths, backslash-only paths, platform encodings/newlines, and
  Windows file-permission assumptions. Remaining Win32 calls are confined to
  guarded Windows compatibility branches.
- Compared literal and generated sound-command names with the case-sensitive
  asset filenames; no Windows-only case mismatches remain.
