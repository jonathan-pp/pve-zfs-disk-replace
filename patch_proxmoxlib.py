#!/usr/bin/env python3
"""
Surgically patch a live, already-built proxmoxlib.js:
  - verify the existing 'Proxmox.window.ZFSDetail' class matches the
    exact upstream version this patch was written against (fails
    loudly instead of guessing if Proxmox changed it since)
  - swap it for the patched version (adds the "Replace Disk" button)
  - append the new 'Proxmox.window.ZFSReplaceDisk' class

Exits non-zero and changes nothing on any mismatch, so a Proxmox VE
update that touched ZFSDetail.js never gets silently clobbered.
"""
import os
import sys
import time


def find_class_block(text, classname):
    marker = f"Ext.define('{classname}', {{"
    start = text.find(marker)
    if start == -1:
        return None
    brace_start = text.index("{", start)
    depth = 0
    in_str = None
    escape = False
    i = brace_start
    while i < len(text):
        c = text[i]
        if in_str:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == in_str:
                in_str = None
        else:
            if c in ("'", '"', "`"):
                in_str = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    j = i + 1
                    while j < len(text) and text[j] in " \t\n":
                        j += 1
                    if text[j : j + 2] == ");":
                        return start, j + 2
                    return start, i + 1
        i += 1
    return None


def main():
    live_path, baseline_path, patched_path, newclass_path = sys.argv[1:5]

    with open(live_path, encoding="utf-8") as f:
        live = f.read()

    with open(newclass_path, encoding="utf-8") as f:
        newclass = f.read().strip()

    if "Ext.define('Proxmox.window.ZFSReplaceDisk'" in live:
        print("already applied, nothing to do")
        return 0

    block = find_class_block(live, "Proxmox.window.ZFSDetail")
    if block is None:
        print(
            "ERROR: could not find Proxmox.window.ZFSDetail in the live "
            "proxmoxlib.js - refusing to touch it.",
            file=sys.stderr,
        )
        return 1
    start, end = block
    current = live[start:end].strip()

    with open(baseline_path, encoding="utf-8") as f:
        baseline = f.read().strip()
    with open(patched_path, encoding="utf-8") as f:
        patched = f.read().strip()

    if current != baseline:
        print(
            "ERROR: the installed ZFSDetail.js does not match the "
            "version this patch was written against (Proxmox likely "
            "updated it). Refusing to overwrite - please check "
            "https://github.com/jonathan-pp/pve-zfs-disk-replace for an "
            "update, or apply the change manually.",
            file=sys.stderr,
        )
        return 1

    # Only ever back up content we've just confirmed is the pristine
    # upstream version - never back up blindly before this check, or a
    # backup taken while the file was already patched (e.g. after a
    # previous .orig got removed) would silently become the "original".
    backup_path = live_path + ".orig"
    if not os.path.exists(backup_path):
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(live)

    new_live = live[:start] + patched + live[end:] + "\n\n" + newclass + "\n"

    # Proxmox's GUI loads this file as proxmoxlib.js?ver=<first line>, so
    # the first line doubles as a cache-busting token. Bump it, or browsers
    # that already fetched the old content under that same URL will keep
    # serving it from cache and never show the new button.
    lines = new_live.split("\n", 1)
    if lines[0].startswith("//"):
        lines[0] += f"-zfsreplace{int(time.time())}"
        new_live = "\n".join(lines)

    with open(live_path, "w", encoding="utf-8") as f:
        f.write(new_live)

    print("patched proxmoxlib.js in place")
    return 0


if __name__ == "__main__":
    sys.exit(main())
