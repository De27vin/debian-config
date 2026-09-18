#!/usr/bin/env python3

from __future__ import annotations

import collections
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PANEL_XML = ROOT / "config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"
PANEL_DIR = ROOT / "config/xfce4/panel"
SHORTCUTS_XML = (
    ROOT
    / "config/xfce4/xfconf/xfce-perchannel-xml/xfce4-keyboard-shortcuts.xml"
)

errors: list[str] = []


def error(message: str) -> None:
    errors.append(message)


def child_property(parent: ET.Element, name: str) -> ET.Element | None:
    return next(
        (child for child in parent.findall("property") if child.get("name") == name),
        None,
    )


try:
    panel_root = ET.parse(PANEL_XML).getroot()
except (OSError, ET.ParseError) as exc:
    print(f"ERROR: cannot parse {PANEL_XML}: {exc}", file=sys.stderr)
    raise SystemExit(1)

panels = child_property(panel_root, "panels")
panel = child_property(panels, "panel-2") if panels is not None else None
plugins = child_property(panel_root, "plugins")
if panel is None or plugins is None:
    print("ERROR: panel-2 or plugins section is missing", file=sys.stderr)
    raise SystemExit(1)

plugin_ids_property = child_property(panel, "plugin-ids")
if plugin_ids_property is None or plugin_ids_property.get("type") != "array":
    error("panel-2/plugin-ids is missing or is not an array")
    plugin_ids: list[int] = []
else:
    plugin_ids = [int(value.get("value", "-1")) for value in plugin_ids_property]

duplicates = [item for item, count in collections.Counter(plugin_ids).items() if count > 1]
if duplicates:
    error(f"duplicate plugin IDs: {duplicates}")

definitions: dict[int, ET.Element] = {}
for prop in plugins.findall("property"):
    name = prop.get("name", "")
    if name.startswith("plugin-") and name[7:].isdigit():
        definitions[int(name[7:])] = prop

missing = sorted(set(plugin_ids) - set(definitions))
unused = sorted(set(definitions) - set(plugin_ids))
if missing:
    error(f"plugin IDs without definitions: {missing}")
if unused:
    error(f"plugin definitions not used by panel-2: {unused}")

expected_plugins = {
    2: "xfce4-clipman-plugin",
    3: "pulseaudio",
    5: "whiskermenu",
    9: "tasklist",
    21: "power-manager-plugin",
}
for plugin_id, expected in expected_plugins.items():
    actual = definitions.get(plugin_id)
    if actual is None or actual.get("value") != expected:
        error(f"plugin-{plugin_id} must be {expected!r}")

for plugin_id in plugin_ids:
    definition = definitions.get(plugin_id)
    if definition is None:
        continue
    plugin_name = definition.get("value", "")
    plugin_desktop = Path("/usr/share/xfce4/panel/plugins") / f"{plugin_name}.desktop"
    if not plugin_desktop.is_file():
        error(f"installed panel plugin desktop file is missing: {plugin_desktop}")

    if plugin_name != "launcher":
        continue
    items = child_property(definition, "items")
    if items is None or items.get("type") != "array":
        error(f"plugin-{plugin_id}/items is missing or is not an array")
        continue
    values = [value.get("value", "") for value in items.findall("value")]
    if not values:
        error(f"plugin-{plugin_id}/items is empty")
    for item in values:
        desktop = PANEL_DIR / f"launcher-{plugin_id}" / item
        if not desktop.is_file():
            error(f"launcher item is missing: {desktop.relative_to(ROOT)}")

if (PANEL_DIR / "launcher-5").exists():
    error("stale launcher-5 directory is present; plugin 5 is Whisker")

whisker = definitions.get(5)
if whisker is not None:
    button_icon = child_property(whisker, "button-icon")
    if button_icon is None or button_icon.get("value") != (
        "/usr/share/icons/hicolor/64x64/emblems/emblem-debian.png"
    ):
        error("Whisker is not configured with the Debian swirl icon")

try:
    shortcuts_root = ET.parse(SHORTCUTS_XML).getroot()
except (OSError, ET.ParseError) as exc:
    error(f"cannot parse keyboard shortcuts: {exc}")
else:
    found_whisker_shortcut = any(
        prop.get("name") == "<Shift><Alt>F1"
        and prop.get("value") == "xfce4-popup-whiskermenu"
        for prop in shortcuts_root.iter("property")
    )
    if not found_whisker_shortcut:
        error("Shift+Alt+F1 does not invoke xfce4-popup-whiskermenu")

for relative in (
    "bin/keep-panel-on-preferred-monitor",
    "bin/move-window-next-monitor",
    "bin/xampp-manager",
    "bin/xcape-super-whisker",
    "systemd/user/xfce-panel-preferred-monitor.service",
    "config/autostart/xcape-super-whisker.desktop",
    "config/autostart/xfce-panel-preferred-monitor.desktop",
):
    if not (ROOT / relative).is_file():
        error(f"required repository file is missing: {relative}")

for icon in (
    "Android-Studio-icon.png",
    "Spotify-icon.png",
    "Telegram-icon.png",
    "Whatsapp-icon.png",
    "XAMPP-icon.png",
):
    if not (ROOT / "icons" / icon).is_file():
        error(f"custom icon is missing: icons/{icon}")

for command in ("gdbus", "flock", "pgrep", "xev", "xfconf-query", "xrandr", "xwininfo"):
    if shutil.which(command) is None:
        error(f"required command is not installed: {command}")

if errors:
    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)

print(f"OK: {len(plugin_ids)} unique panel plugins and all managed files validated")
