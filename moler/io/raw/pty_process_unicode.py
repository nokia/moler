# -*- coding: utf-8 -*-
__author__ = "Marcin Usielski"
__copyright__ = "Copyright (C) 2026, Nokia"
__email__ = "marcin.usielski@nokia.com"

import codecs
import fcntl
import os
import pty
import shlex
import subprocess
import time

from typing import Optional, Tuple, Union

from moler.exceptions import MolerException

# Unix only. Does not work on Windows.


class PtyProcessUnicodeNotFork:
    """PtyProcessUnicode without forking process."""
    def __init__(self, cmd: str = "/bin/bash", dimensions: Tuple[int, int] = (25, 120), buffer_size: int = 4096):
        """
        Initialize PtyProcessUnicodeNotFork.
        :param cmd: command to run in pty process
        :param dimensions: dimensions of the pty (rows, cols)
        :param buffer_size: buffer size for reading data
        """
        self.cmd: str = cmd
        self.dimensions: Tuple[int, int] = dimensions
        self.buffer_size: int = buffer_size
        self.delayafterclose: float = 0.2
        self.encoding = "utf-8"
        self.decoder = codecs.getincrementaldecoder(self.encoding)(errors='strict')
        self.fd: int = -1  # File descriptor for pty master
        self.pid: int = -1  # Process ID of the child process
        self.slave_fd: int = -1  # File descriptor for pty slave
        self.process: Optional[subprocess.Popen] = None  # Subprocess.Popen object
        self._closed: bool = True

    def create_pty_process(self) -> None:
        """Create PtyProcessUnicode without forking process."""

        # Create a new pty pair
        master_fd, slave_fd = pty.openpty()

        # Set master fd to non-blocking mode
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        # Start the subprocess with the slave fd
        process = subprocess.Popen(
            shlex.split(self.cmd),
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            start_new_session=True
        )

        # Store the process information
        self.fd = master_fd
        self.slave_fd = slave_fd
        self.pid = process.pid
        self.process = process
        self._closed = False

        time.sleep(0.1)

    def write(self, data: Union[str, bytes]) -> int:
        """
        Write data to pty process.
        :param data: data to write
        :return: number of bytes written
        """
        if self._closed or self.fd < 0:
            raise MolerException("Cannot write to closed pty process")

        try:
            # Convert string to bytes if necessary
            if isinstance(data, str):
                data_bytes = data.encode(self.encoding, errors='ignore')
            else:
                data_bytes = data

            # Write data to the pty master
            written = os.write(self.fd, data_bytes)
            return written
        except OSError as e:
            if e.errno == 5:  # Input/output error - process might be dead
                self.close(force=True)
                self._closed = True
            raise

    def read(self, size: int) -> str:
        """
        Read data from pty process.
        :param size: number of bytes to read
        :return: data read as string
        """
        if self._closed or self.fd < 0:
            raise MolerException("Cannot read from closed pty process")

        try:
            # Read raw bytes from pty master (non-blocking)
            data_bytes = os.read(self.fd, size)

            if not data_bytes:
                raise MolerException("End of file reached")

            # Decode bytes to string using the incremental decoder
            # This handles partial UTF-8 sequences correctly
            data_str = self.decoder.decode(data_bytes, final=False)
            return data_str

        except OSError as e:
            if e.errno == 11:  # Resource temporarily unavailable (EAGAIN)
                return ""  # No data available, return empty string
            elif e.errno == 5:  # Input/output error - process might be dead
                self.close(force=True)
                raise MolerException("End of file reached")
            else:
                raise

    def close(self, force: bool = False) -> None:
        """
        Close pty process.
        :param force: if True, forcefully kill the process
        :return: None
        """
        if self._closed:
            return
        self._closed = True

        # Try to terminate the process gracefully first
        if self.process and self.isalive():
            try:
                if force:
                    self.process.kill()  # SIGKILL
                else:
                    self.process.terminate()  # SIGTERM

                # Wait for process to end with timeout
                try:
                    self.process.wait(timeout=self.delayafterclose)
                except subprocess.TimeoutExpired:
                    if not force:
                        # If still alive and not forcing, try kill
                        self.process.kill()
                        self.process.wait(timeout=0.5)
            except Exception as e:
                print(f"Error terminating process: {e}")

        # Close file descriptors
        if self.fd >= 0:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = -1

        if self.slave_fd >= 0:
            try:
                os.close(self.slave_fd)
            except OSError:
                pass
            self.slave_fd = -1

    def isalive(self) -> bool:
        """
        Check if pty process is alive.
        :return: True if process is alive, False otherwise
        """
        if self._closed or not self.process:
            return False

        # Check if process is still running
        poll_result = self.process.poll()
        return poll_result is None  # None means process is still running
