#!/usr/bin/env bash
#
# Reverts install.sh: restores the original ZFS.pm / proxmoxlib.js from
# their .orig backups.
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/jonathan-pp/pve-zfs-disk-replace/main/uninstall.sh)"

set -euo pipefail

ZFSPM=/usr/share/perl5/PVE/API2/Disks/ZFS.pm
PROXMOXLIB=/usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js

for f in "$ZFSPM" "$PROXMOXLIB"; do
    if [ -f "$f.orig" ]; then
        cp -a "$f.orig" "$f"
        echo "restored $f"
    else
        echo "no backup found for $f, leaving as-is" >&2
    fi
done

systemctl restart pvedaemon pveproxy
echo "done."
