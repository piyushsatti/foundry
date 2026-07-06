---
name: reference-nvidia-vgl-device-perms-ubuntu
description: "make /dev/nvidia* group-owned by vglusers persistently on Ubuntu — only a udev RUN+= rule on the PCI event works"
metadata:
  node_type: memory
  type: reference
  last_updated: 2026-06-20
  originSessionId: f634cf24-4437-480e-b3c1-49acaf5b21d0
---

To give a Unix group (e.g. `vglusers` for VirtualGL) access to `/dev/nvidia0` + `/dev/nvidiactl` **persistently** on Ubuntu (hybrid Intel+NVIDIA, PRIME on-demand, 580-open), the ONLY robust mechanism is a **udev `RUN+=` rule on the nvidia PCI driver add event**:

```
# /etc/udev/rules.d/72-nvidia-vglusers.rules  (numbered >71 so it runs after stock 71-nvidia.rules)
ACTION=="add", DEVPATH=="/bus/pci/drivers/nvidia", RUN+="/bin/sh -c 'chgrp vglusers /dev/nvidia[0-9]* /dev/nvidiactl /dev/nvidia-modeset 2>/dev/null || true'"
ACTION=="add", SUBSYSTEM=="module", KERNEL=="nvidia_uvm", RUN+="/bin/sh -c 'chgrp vglusers /dev/nvidia-uvm /dev/nvidia-uvm-tools 2>/dev/null || true'"
```
`sudo udevadm control --reload-rules`. Confirmed working across reboot + RTD3 wake on 26.04 (systemd 259).

**Why the obvious approaches FAIL (took 4 attempts):**
- ❌ `KERNEL=="nvidia0", GROUP="vglusers"` udev rule — `/dev/nvidia0` is **NOT udev-managed** (`udevadm info --name=/dev/nvidia0` returns nothing), so the rule never fires.
- ❌ `NVreg_DeviceFileGID=<gid>` modprobe param — Ubuntu's `/sbin/ub-device-create` (replaced upstream `nvidia-modprobe` via Launchpad #1839309) **hardcodes root:root** and ignores the GID param. Mode (0660) applies because the kernel enforces it; GID never does. (The param only works with upstream `nvidia-modprobe`, which Ubuntu doesn't use. VirtualGL's `vglserver_config` relies on this param → also doesn't cover `/dev/nvidia*` on Ubuntu.)
- ❌ systemd oneshot `After=nvidia-persistenced` — races the async node creation (node appears ~1s after the service runs).
- ❌ systemd `.path` `PathExists=/dev/nvidia0` — works at boot but misses RTD3 mid-session resets (node persists in devtmpfs so PathExists never re-fires when the GPU powers down and ub-device-create resets perms).

**Why the PCI-event RUN+= works:** the PCI device IS udev-tracked; `RUN+=` executes synchronously right after `ub-device-create` in the same event, and re-fires on every driver rebind (RTD3 wake). Matches SUSEPrime/Arch per-event-fixup patterns.

Context: this machine runs VirtualGL 3.1.1 (panorama/ladybug EGL rendering). GID 1002 = vglusers. Full saga in `~/Documents/notes/journal/2026-06-20-ubuntu-26.04-migration-runbook.md`. Related: [[reference-linux-package-manager-strategy]], [[project-portable-dev-machine-north-star]].
