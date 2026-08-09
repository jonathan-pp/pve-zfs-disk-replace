#!/usr/bin/env python3
"""
Replace a live file with a patched version, but only if it still matches
the exact upstream version this patch was written against. Exits non-zero
and changes nothing on any mismatch, so a Proxmox VE update that touched
the file never gets silently clobbered with a stale snapshot.
"""
import os
import sys


def main():
    live_path, baseline_path, patched_path, marker = sys.argv[1:5]

    with open(live_path, encoding="utf-8") as f:
        live = f.read()

    if marker in live:
        print(f"{live_path}: already applied, nothing to do")
        return 0

    with open(baseline_path, encoding="utf-8") as f:
        baseline = f.read()

    if live != baseline:
        print(
            f"ERROR: {live_path} does not match the exact upstream version "
            "this patch was written against (Proxmox likely updated it). "
            "Refusing to overwrite - check "
            "https://github.com/jonathan-pp/pve-zfs-disk-replace for an "
            "update, or apply the change manually.",
            file=sys.stderr,
        )
        return 1

    with open(patched_path, encoding="utf-8") as f:
        patched = f.read()

    # Only ever back up content we've just confirmed is the pristine
    # upstream version - never back up blindly before this check, or a
    # backup taken while the file was already patched (e.g. after a
    # previous .orig got removed) would silently become the "original".
    backup_path = live_path + ".orig"
    if not os.path.exists(backup_path):
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(live)

    with open(live_path, "w", encoding="utf-8") as f:
        f.write(patched)

    print(f"patched {live_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
