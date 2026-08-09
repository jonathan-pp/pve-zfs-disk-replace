#!/usr/bin/env bash
#
# Adds GUI-driven ZFS "Replace Disk" support to an existing Proxmox VE 9.x
# node: Datacenter > Node > Disks > ZFS > (pool) > Detail gets a "Replace
# Disk" button, enabled when a non-ONLINE device is selected.
#
# Run this directly ON the Proxmox VE node, as root:
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/jonathan-pp/pve-zfs-disk-replace/main/install.sh)"
#
# Source / issue tracker: https://github.com/jonathan-pp/pve-zfs-disk-replace
#
# IMPORTANT: this patches the *currently installed* ZFS.pm / proxmoxlib.js
# in place, only after verifying they still match the exact upstream
# version this patch was written against. If a Proxmox VE update changed
# either file, the corresponding step fails loudly and changes nothing,
# instead of silently reverting an upstream fix with a stale snapshot.
#
# Idempotent: safe to re-run (e.g. after a Proxmox VE update reset the
# files). Keeps a *.orig backup of each file, taken at the exact moment
# its content is confirmed pristine (never backed up blindly), so
# uninstall.sh can always restore the real original.

set -euo pipefail

ZFSPM=/usr/share/perl5/PVE/API2/Disks/ZFS.pm
PROXMOXLIB=/usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js

if [ ! -f "$ZFSPM" ] || [ ! -f "$PROXMOXLIB" ]; then
    echo "This does not look like a Proxmox VE node (missing $ZFSPM or $PROXMOXLIB)." >&2
    exit 1
fi

RAW="https://raw.githubusercontent.com/jonathan-pp/pve-zfs-disk-replace/main"
WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

echo "==> fetching patch files"
for f in ZFS.pm.orig ZFS.pm.patched ZFSDetail.orig.js ZFSDetail.patched.js \
         ZFSReplaceDisk.js safe_replace.py patch_proxmoxlib.py; do
    curl -fsSL "$RAW/$f" -o "$WORKDIR/$f"
done

echo "==> patching $ZFSPM"
python3 "$WORKDIR/safe_replace.py" \
    "$ZFSPM" "$WORKDIR/ZFS.pm.orig" "$WORKDIR/ZFS.pm.patched" "name => 'replace'"
perl -c "$ZFSPM"

echo "==> patching $PROXMOXLIB"
python3 "$WORKDIR/patch_proxmoxlib.py" \
    "$PROXMOXLIB" "$WORKDIR/ZFSDetail.orig.js" "$WORKDIR/ZFSDetail.patched.js" "$WORKDIR/ZFSReplaceDisk.js"

systemctl restart pvedaemon pveproxy
sleep 1
systemctl is-active --quiet pvedaemon pveproxy

echo "==> done. Disks > ZFS > (pool) > Detail now has a 'Replace Disk' button."
echo "    Originals backed up as *.orig next to each file if you need to revert."
