#!/bin/bash

set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
state_home=${XDG_STATE_HOME:-$HOME/.local/state}
timestamp=$(date +%Y%m%d-%H%M%S)
backup_dir=$state_home/debian-config/backups/$timestamp
enable_service=1

usage() {
  cat <<'EOF'
Usage: ./install.sh [--no-enable]

Run this from a text console while the XFCE session is logged out. Existing
managed files are backed up under ~/.local/state/debian-config/backups/.
EOF
}

for argument in "$@"; do
  case $argument in
    --no-enable)
      enable_service=0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

if ((EUID == 0)); then
  printf 'Run this installer as the desktop user, not root.\n' >&2
  exit 1
fi

xfconf_active=0
if pgrep -u "$(id -u)" -x xfconfd >/dev/null 2>&1; then
  xfconf_active=1
elif gdbus call --session \
  --dest org.freedesktop.DBus \
  --object-path /org/freedesktop/DBus \
  --method org.freedesktop.DBus.NameHasOwner \
  org.xfce.Xfconf 2>/dev/null | grep -q true; then
  xfconf_active=1
fi

if ((xfconf_active)); then
  printf 'xfconfd is running. Log out of XFCE and run this from a text console.\n' >&2
  exit 1
fi

"$repo_dir/scripts/validate-config.py"

mkdir -p "$backup_dir"

backup_file() {
  local target=$1
  local relative=${target#"$HOME"/}

  [[ -e $target || -L $target ]] || return 0
  mkdir -p "$backup_dir/home/$(dirname "$relative")"
  cp -a "$target" "$backup_dir/home/$relative"
}

panel_target=$HOME/.config/xfce4/panel
if [[ -d $panel_target ]]; then
  mkdir -p "$backup_dir/home/.config/xfce4"
  mv "$panel_target" "$backup_dir/home/.config/xfce4/panel"
fi
mkdir -p "$panel_target"
cp -a "$repo_dir/config/xfce4/panel/." "$panel_target/"

while IFS= read -r -d '' source; do
  relative=${source#"$repo_dir/config/"}
  target=$HOME/.config/$relative
  backup_file "$target"
  install -Dm644 "$source" "$target"
done < <(find "$repo_dir/config" -type f ! -path '*/xfce4/panel/*' -print0)

while IFS= read -r -d '' source; do
  target=$HOME/.local/bin/$(basename "$source")
  backup_file "$target"
  install -Dm755 "$source" "$target"
done < <(find "$repo_dir/bin" -maxdepth 1 -type f -print0)

service_target=$HOME/.config/systemd/user/xfce-panel-preferred-monitor.service
backup_file "$service_target"
install -Dm644 \
  "$repo_dir/systemd/user/xfce-panel-preferred-monitor.service" \
  "$service_target"

icon_root=$HOME/.local/share/icons/hicolor/256x256/apps
mkdir -p "$icon_root"
for source in "$repo_dir"/icons/*.png; do
  install -m644 "$source" "$icon_root/$(basename "$source")"
done
if [[ ! -f $HOME/.local/share/icons/hicolor/index.theme ]]; then
  install -Dm644 /usr/share/icons/hicolor/index.theme \
    "$HOME/.local/share/icons/hicolor/index.theme"
fi
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null

if ((enable_service)); then
  systemctl --user daemon-reload
  systemctl --user enable xfce-panel-preferred-monitor.service
fi

printf 'Installed Debian XFCE configuration.\nBackup: %s\n' "$backup_dir"
printf 'The monitor helper will start with the next XFCE login.\n'
