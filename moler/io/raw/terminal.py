import select
import time
from threading import Thread

from ptyprocess import PtyProcessUnicode

from moler.connection import ObservableConnection


class Terminal(Thread, ObservableConnection):
    def __init__(self, cmd='/bin/bash', select_timeout=0.002, read_buffer_size=4096):
        self._cmd = [cmd]
        self._select_timeout = select_timeout
        self._read_buffer_size = read_buffer_size
        self._terminal = None
        self._exit = False

        self._terminal = PtyProcessUnicode.spawn(self._cmd)
        self.send("TERM=xterm-mono bash")
        time.sleep(0.1)
        Thread.__init__(self)
        ObservableConnection.__init__(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # reraise exceptions if any

    def close(self, wait=True):
        self._exit = True
        if wait:
            while self._exit:
                time.sleep(self._select_timeout / 10.)

    def send(self, cmd, newline="\n"):
        self._terminal.write(cmd)
        if newline:
            self._terminal.write(newline)

    def run(self, ):
        self._main_loop()
        self._terminal.wait()

    def _main_loop(self):
        while True:
            reads, _, _ = select.select([self._terminal.fd], [], [], self._select_timeout)
            if self._terminal.fd in reads:
                if not self._read_from_terminal():
                    break
            if self._exit:
                self._exit = False
                break

    def _read_from_terminal(self):
        try:
            data = self._terminal.read(self._read_buffer_size)
            self.data_received(data)
        except EOFError:
            return False

        return True


if __name__ == "__main__":
    pass
