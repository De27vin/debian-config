# Debian XFCE configuration

This repository versions Devin's Debian 13 XFCE panel, launchers, Whisker Menu, keyboard shortcut, custom icons, and primary-monitor handling.

## History and safety checkpoint

Commit `6f1f65a` is a literal snapshot of the working system before cleanup. It intentionally contains the original unsafe monitor helper, the stale duplicate `launcher-5`, and known-broken historical XML under `archive/`. Keep that commit as the recovery checkpoint; never restore `archive/xfce4-panel.xml.BROKEN` or `archive/xfce-panel-backup/` wholesale.

The old configurations contained undefined plugin references and launcher `items` values with the wrong scalar type. Those defects caused the recurring `Plugin "(null)"` dialog and gear icons. The active configuration now has one definition for every listed plugin and all launcher `items` values are arrays.

## Managed components

| Repository path | Installation path |
| --- | --- |
| `config/xfce4/xfconf/xfce-perchannel-xml/` | `~/.config/xfce4/xfconf/xfce-perchannel-xml/` |
| `config/xfce4/panel/` | `~/.config/xfce4/panel/` |
| `config/autostart/` | `~/.config/autostart/` |
| `systemd/user/` | `~/.config/systemd/user/` |
| `bin/` | `~/.local/bin/` |
| `icons/` | `~/.local/share/icons/hicolor/256x256/apps/` |
| `archive/` | Historical reference only; never installed |

The panel contains Whisker Menu; launchers for Terminal, Firefox ESR, Telegram, WhatsApp, Spotify, Prism Launcher, XAMPP, VS Code, and Android Studio; Window Buttons for running applications; a workspace pager; Clipman; CPU graph; system tray; PulseAudio; Power Manager; and a clock. Whisker is plugin 5 and uses the Debian swirl icon. Window Buttons is tasklist plugin 9 and shows applications from all workspaces. XAMPP is launcher plugin 35.

## Dependencies

Panel and helper packages:

```text
xfce4-panel
xfce4-whiskermenu-plugin
xfce4-clipman-plugin
xfce4-cpugraph-plugin
xfce4-pulseaudio-plugin
xfce4-power-manager-plugins
xfce4-terminal
xfconf
x11-utils
x11-xserver-utils
libglib2.0-bin
procps
util-linux
zenity
pkexec
xcape
```

`xcape-super-whisker` supports either Debian's `/usr/bin/xcape` or the existing local installation at `~/.local/xcape/usr/bin/xcape`.

Application launchers additionally expect:

- Firefox ESR and Visual Studio Code;
- Android Studio at `/opt/android-studio`;
- Telegram, Spotify, and WhatsApp Electron snaps;
- Prism Launcher installed system-wide through Flatpak;
- XAMPP at `/opt/lampp`.

The XAMPP launcher uses `~/.local/bin/xampp-manager`, a Zenity front end to `/opt/lampp/xampp`. Privileged actions are authenticated through `pkexec`; it does not depend on the missing legacy `manager-linux-x64.run` binary.

## Validate

Run the repository validator before installing:

```sh
./scripts/validate-config.py
```

It checks plugin-ID consistency, required plugin desktop identifiers, launcher arrays and files, Whisker configuration, the Super-key shortcut, helper files, icons, and required commands.

Desktop entries and shell syntax can also be checked with:

```sh
desktop-file-validate config/autostart/*.desktop config/xfce4/panel/launcher-*/*.desktop
bash -n bin/* install.sh
```

## Install or restore

Installing panel XML while `xfconfd` is running is unsafe because the daemon may overwrite it. Log out of XFCE, switch to a text console, clone this repository, and run:

```sh
./install.sh
```

The installer refuses to proceed while `xfconfd` is running. It backs up every managed destination under:

```text
~/.local/state/debian-config/backups/YYYYmmdd-HHMMSS/
```

It installs icons in the user's icon theme, so root access is not required. The monitor service is enabled for the next XFCE login. Use `--no-enable` to leave it disabled.

## Super key and Whisker

`config/autostart/xcape-super-whisker.desktop` starts `~/.local/bin/xcape-super-whisker`. Tapping Super emits `Shift+Alt+F1`; the XFCE keyboard-shortcuts channel maps that shortcut to `xfce4-popup-whiskermenu`. Modifier combinations using Super remain available.

## Primary-monitor behavior

Panel 2 uses XFCE's native `output-name=Primary`, not a connector-specific name such as DP-1. XFCE Display Settings controls which monitor is primary, and its saved display profile can restore the desired physical layout.

The custom service remains necessary as a narrow compatibility guard because Debian 13 currently ships `xfce4-panel 4.20.4`, which has an upstream hotplug regression. Upstream 4.20.5 includes the fix “panel: Show window when new output is connected.”

The replacement helper:

1. waits for an XFCE X11 session, xfconf, the panel D-Bus name, and exactly one panel process;
2. obtains session environment dynamically, with no fixed `DISPLAY` or Xauthority path;
3. holds a singleton lock in `$XDG_RUNTIME_DIR`;
4. listens for XRandR events through `xev` instead of polling;
5. debounces event bursts for three seconds;
6. reasserts native `Primary` only when necessary;
7. verifies the visible panel window is geometrically inside the primary output;
8. does nothing when placement is correct;
9. after five failed checks on a stable topology, may request one restart through the existing panel's D-Bus interface;
10. rate-limits that fallback to once every five minutes and never starts `xfce4-panel` itself.

The unit has a 64 MB memory limit, a 16-task limit, retained journal output, and a 15-second systemd failure backoff. The XDG autostart entry restarts only the helper after XFCE login so it receives the current session environment.

### Service commands

```sh
systemctl --user status xfce-panel-preferred-monitor.service
systemctl --user enable --now xfce-panel-preferred-monitor.service
systemctl --user disable --now xfce-panel-preferred-monitor.service
journalctl --user -u xfce-panel-preferred-monitor.service -b
```

Run a non-watching placement check with panel restart disabled:

```sh
PANEL_ALLOW_RESTART=0 ~/.local/bin/keep-panel-on-preferred-monitor --once
```

## Troubleshooting

- `Plugin "(null)"`: validate that every ID in `/panels/panel-2/plugin-ids` has exactly one `/plugins/plugin-ID` definition. Do not restore files from `archive/`.
- Gear launcher icons: ensure `/plugins/plugin-ID/items` is an array, not a string.
- Panel on the wrong monitor: confirm XRandR has exactly one primary output and panel `output-name` is `Primary`; then inspect the helper journal.
- Missing custom icon: run `gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor`.
- Super does not open Whisker: run `~/.local/bin/xcape-super-whisker --check`, confirm the xcape process exists, and validate the `Shift+Alt+F1` shortcut.
- XAMPP launcher fails: run `~/.local/bin/xampp-manager --check` and confirm `/opt/lampp/xampp` is executable.

Do not solve panel-placement problems by restoring old XML, repeatedly invoking `xfce4-panel --restart`, or starting another panel process.
