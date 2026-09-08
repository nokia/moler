# -*- coding: utf-8 -*-
__author__ = "Marcin Usielski"
__copyright__ = "Copyright (C) 2026, Nokia"
__email__ = "marcin.usielski@nokia.com"

import logging
import os
import sys

from pty import openpty
from time import sleep
from typing import Optional, Tuple

# Unix only. Does not work on Windows.
# openpty/sleep are imported as module-level names so tests can patch them here
# without replacing the attributes of the shared pty/time modules process-wide.

_OPENPTY_RETRY_DELAY_S = 3.0
_OPENPTY_MAX_ATTEMPTS = 2  # first try + one retry after delay

_LINUX_PTY_NR_PATH = "/proc/sys/kernel/pty/nr"
_LINUX_PTY_MAX_PATH = "/proc/sys/kernel/pty/max"
_DARWIN_PTMX_MAX_SYSCTL = "kern.tty.ptmx_max"
_FREEBSD_PTS_MAX_SYSCTL = "kern.pts.max"


def _read_int_file(path: str) -> Optional[int]:
    try:
        with open(path, encoding="ascii") as fh:
            return int(fh.read().strip())
    except (OSError, ValueError):
        return None


def _sysctl_int_byname(name: str) -> Optional[int]:
    """Read an integer sysctl by name (macOS / BSD)."""
    try:
        import ctypes
        import ctypes.util

        libc_name = ctypes.util.find_library("c")
        if libc_name is None:
            return None
        libc = ctypes.CDLL(libc_name, use_errno=True)
        value = ctypes.c_int()
        size = ctypes.c_size_t(ctypes.sizeof(ctypes.c_int))
        rc = libc.sysctlbyname(
            name.encode("ascii"),
            ctypes.byref(value),
            ctypes.byref(size),
            None,
            0,
        )
        if rc == 0:
            return int(value.value)
    except Exception:
        return None
    return None


def _count_dev_ttys() -> Optional[int]:
    """Count macOS PTY slave nodes (/dev/ttys000, ...)."""
    try:
        return sum(
            1
            for entry in os.listdir("/dev")
            if entry.startswith("ttys") and entry[4:].isdigit()
        )
    except OSError:
        return None


def _count_dev_pts() -> Optional[int]:
    """Count FreeBSD PTY slave nodes (/dev/pts/0, /dev/pts/1, ...)."""
    try:
        return sum(1 for entry in os.listdir("/dev/pts") if entry.isdigit())
    except OSError:
        return None


def _get_pty_usage() -> Tuple[Optional[int], Optional[int]]:
    """
    Return (in_use, maximum) PTY counts for this host when known.

    Linux: /proc/sys/kernel/pty/nr and /proc/sys/kernel/pty/max.
    macOS: number of /dev/ttys* nodes and kern.tty.ptmx_max.
    FreeBSD: number of /dev/pts/* nodes and kern.pts.max.
    Other platforms: (None, None).
    """
    plat = sys.platform.lower()
    if plat.startswith("linux"):
        return _read_int_file(_LINUX_PTY_NR_PATH), _read_int_file(_LINUX_PTY_MAX_PATH)
    if plat == "darwin":
        return _count_dev_ttys(), _sysctl_int_byname(_DARWIN_PTMX_MAX_SYSCTL)
    if plat.startswith("freebsd"):
        return _count_dev_pts(), _sysctl_int_byname(_FREEBSD_PTS_MAX_SYSCTL)
    return None, None


def _format_pty_usage() -> str:
    """Human-readable PTY usage snapshot for logs."""
    used, maximum = _get_pty_usage()
    if used is None and maximum is None:
        return "pty devices in use: unknown"
    used_s = str(used) if used is not None else "?"
    max_s = str(maximum) if maximum is not None else "?"
    return f"pty devices in use: {used_s}/{max_s}"


def openpty_with_retry(
    delay_s: float = _OPENPTY_RETRY_DELAY_S,
    max_attempts: int = _OPENPTY_MAX_ATTEMPTS,
    logger: Optional[logging.Logger] = None,
) -> Tuple[int, int]:
    """
    Open a pty master/slave pair.

    On some systems pty.openpty() can raise OSError("out of pty devices") when
    the pool is temporarily exhausted. Wait and retry once in that case.
    """
    log = logger if logger is not None else logging.getLogger(__name__)
    last_exc: Optional[OSError] = None
    for attempt in range(1, max_attempts + 1):
        try:
            return openpty()
        except OSError as exc:
            last_exc = exc
            if "out of pty device" not in str(exc).lower():
                raise
            try:
                usage = _format_pty_usage()
            except Exception as e:
                usage = f"error formatting pty usage: {e}"
            if attempt >= max_attempts:
                log.warning(
                    f"openpty failed: {exc} ({usage}). Giving up after "
                    f"{attempt}/{max_attempts} attempts."
                )
                break
            log.warning(
                f"openpty failed: {exc} ({usage}). Waiting {delay_s}s before retry "
                f"({attempt}/{max_attempts})."
            )
            sleep(delay_s)
    assert last_exc is not None
    raise last_exc
