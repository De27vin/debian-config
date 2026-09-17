# Debian XFCE configuration

This repository versions the user configuration for Devin's Debian 13 XFCE desktop. It focuses on the XFCE panel, Whisker Menu, panel launchers, the Super-key Whisker shortcut, custom launcher icons, and primary-monitor panel handling.

## Baseline state

The initial commit is a literal snapshot of the working system on 2026-09-18. It intentionally preserves historical and harmless debris so that it can serve as a known-good recovery point:

- panel 2 is working with Whisker Menu as plugin 5;
- the XAMPP launcher is active as plugin 35;
- the obsolete duplicate `launcher-5` directory is still present;
- launcher item properties are arrays;
- the Debian swirl is the Whisker button icon;
- the primary-monitor helper and its user service are present in their original form;
- `xfce-panel-preferred-monitor.service` is disabled and inactive because that implementation can race XFCE startup and restart the panel repeatedly.

The files under `archive/` are retained only for diagnosis and history. They contain known-broken panel configurations and must not be restored wholesale.

## Repository layout

| Repository path | Installation path |
| --- | --- |
| `config/xfce4/xfconf/xfce-perchannel-xml/` | `~/.config/xfce4/xfconf/xfce-perchannel-xml/` |
| `config/xfce4/panel/` | `~/.config/xfce4/panel/` |
| `config/autostart/` | `~/.config/autostart/` |
| `systemd/user/` | `~/.config/systemd/user/` |
| `bin/` | `~/.local/bin/` |
| `icons/` | `/usr/share/pixmaps/` |
| `archive/` | Historical reference only; do not install |

## What is configured

The panel contains Whisker Menu; launchers for Terminal, Firefox ESR, Telegram, WhatsApp, Spotify, Prism Launcher, XAMPP, VS Code, and Android Studio; a workspace pager; Clipman; CPU graph; system tray; PulseAudio; Power Manager; and a clock.

`config/autostart/xcape-super-whisker.desktop` uses a locally installed `xcape` executable to translate a tap of the Super key to `Shift+Alt+F1`. The corresponding XFCE keyboard shortcut runs `xfce4-popup-whiskermenu`.

## Dependencies

Core components include:

- Debian 13 with an X11 XFCE session
- `xfce4-panel`
- `xfce4-whiskermenu-plugin`
- `xfce4-clipman-plugin`
- `xfce4-cpugraph-plugin`
- `xfce4-pulseaudio-plugin`
- `xfce4-power-manager`
- `xfce4-terminal`
- `x11-xserver-utils` for `xrandr`
- `xcape` installed at `~/.local/xcape/usr/bin/xcape`

Launcher-specific dependencies include Firefox ESR, Visual Studio Code, Android Studio under `/opt/android-studio`, Telegram/Spotify/WhatsApp snaps, and the Prism Launcher Flatpak. The baseline XAMPP launcher points to `/opt/lampp/manager-linux-x64.run`; that target is currently missing or non-executable and will be addressed after the baseline.

## Manual restore notes

Do not copy the archived XML or `xfce-panel-backup` over the live configuration. The archive includes undefined plugin references that previously caused a recurring `Plugin "(null)"` dialog.

Before restoring active files, stop making panel changes and take a backup of the destination. Restore the active `config/` trees to their mapped locations, copy scripts with executable permissions, and install the icons under `/usr/share/pixmaps/`. Panel configuration should be applied while XFCE's configuration daemon is handled deliberately; a deterministic installer will be added in a later commit.

The baseline monitor service must remain disabled:

```sh
systemctl --user disable --now xfce-panel-preferred-monitor.service
```

Do not enable it until the safer implementation in a later commit has been installed and tested.
