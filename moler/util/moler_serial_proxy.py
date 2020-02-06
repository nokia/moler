import serial
import serial.threaded
import threading
import time
import sys
import platform
import traceback
from contextlib import contextmanager
try:
    input = raw_input
except NameError:
    pass

hostname = platform.node()


class IOSerial(object):
    """Serial-IO connection."""
    def __init__(self, port, baudrate=115200, stopbits=serial.STOPBITS_ONE,
                 parity=serial.PARITY_NONE, timeout=2, xonxoff=1):
        self.port = port
        self.baudrate = baudrate
        self.stopbits = stopbits
        self.parity = parity
        self.timeout = timeout
        self.xonxoff = xonxoff
        self._serial_connection = None

    def open(self):
        """
        Take 'how to establish connection' info from constructor
        and open that connection.

        Return context manager to allow for:  with connection.open() as conn:
        """
        self._serial_connection = serial.Serial(port=self.port,
                                                baudrate=self.baudrate,
                                                stopbits=self.stopbits,
                                                parity=self.parity,
                                                timeout=self.timeout,
                                                xonxoff=self.xonxoff)
        return self

    def close(self):
        """Close established connection."""
        self._serial_connection.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # reraise exceptions if any

    def send(self, cmd):
        """Sends data over serial connection"""
        self._serial_connection.write(cmd)
        self._serial_connection.flush()

    def read(self):
        """Returns data read from serial connection"""
        # read all that is there or wait for one byte (blocking)
        data = self._serial_connection.read(self._serial_connection.in_waiting or 1)
        return data


class IoThreadedSerial(IOSerial):
    """Threaded Serial-IO connection."""
    def __init__(self, port, protocol_factory, baudrate=115200, stopbits=serial.STOPBITS_ONE,
                 parity=serial.PARITY_NONE, timeout=2, xonxoff=1):
        super(IoThreadedSerial, self).__init__(port=port, baudrate=baudrate, stopbits=stopbits,
                                               parity=parity, timeout=timeout, xonxoff=xonxoff)
        self.pulling_thread = None
        self.protocol_factory = protocol_factory
        self.transport = None
        self.protocol = None

    def open(self):
        """
        Take 'how to establish connection' info from constructor
        and open that connection.

        Return context manager to allow for:  with connection.open() as conn:
        """
        super(IoThreadedSerial, self).open()
        self.pulling_thread = serial.threaded.ReaderThread(self._serial_connection, self.protocol_factory)
        self.pulling_thread.start()
        transport, protocol = self.pulling_thread.connect()
        self.transport = transport
        self.protocol = protocol
        return self

    def close(self):
        """Close the serial port and exit reader thread"""
        if self.pulling_thread:
            self.pulling_thread.close()
            self.pulling_thread = None

    def send(self, cmd):
        """Sends data over serial connection"""
        self.protocol.send(cmd)

    def send_and_await_response(self, line, response, timeout=4):
        with self.protocol.send_and_await_response(line, response, timeout) as response_found:
            pass


class AtToStdout(serial.threaded.LineReader):
    """ATserial->stdout"""

    def __init__(self, prefix, verbose=False):
        super(AtToStdout, self).__init__()
        self.prefix = prefix
        self.verbose = verbose
        self.awaited_output = None
        self._await = threading.Event()
        self._found = threading.Event()

    def __call__(self):  # make it protocol_factory for itself
        return self

    def connection_made(self, transport):
        super(AtToStdout, self).connection_made(transport)
        msg = "{}  opened".format(self.prefix)
        sys.stdout.write('{}\n'.format(msg))

    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)
        msg = "{}  closed".format(self.prefix)
        sys.stdout.write('{}\n'.format(msg))

    def handle_line(self, line):
        if self.verbose:
            print("received line: {!r}".format(line))
        print(line)
        if self._await.is_set():
            if self.awaited_output and (self.awaited_output in line):
                if self.verbose:
                    print("found {!r} in {!r}".format(self.awaited_output, line))
                self._found.set()

    def send(self, line):
        if self.verbose:
            print("sending line: {!r}".format(line))
        super(AtToStdout, self).write_line(line)
        # self.transport.serial.flush()  # TODO: do we need it

    @contextmanager
    def send_and_await_response(self, line, response, timeout=4):
        """Await till data comes"""
        # to be used in "sender thread"
        try:
            if self.verbose:
                print("will await: {!r}".format(response))
            self.awaited_output = response
            self._found.clear()
            self._await.set()

            self.send(line)

            response_found = self._found.wait(timeout)
            if self.verbose:
                print("{!r} {!r} response_found: {!r}".format(line, response, response_found))
            self._found.clear()
            self._await.clear()
            yield response_found
        finally:
            self.awaited_output = None
            self._found.clear()
            self._await.clear()


class AtConsoleProxy(object):
    """Class to proxy AT commands console into stdin/stdout"""
    def __init__(self, port, verbose=False):
        ser_to_stdout = AtToStdout("{}:{}  port".format(hostname, port), verbose=verbose)
        self._serial_io = IoThreadedSerial(port=port, protocol_factory=ser_to_stdout)
        self.verbose = verbose

    def open(self):
        """
        Open underlying serial connection.

        Return context manager to allow for:  with connection.open() as conn:
        """
        print("{}  opening serial port {}".format(hostname, self._serial_io.port))
        self._serial_io.open()

        self._apply_initial_configuration()

        return self

    def _apply_initial_configuration(self):
        # activate echo of AT commands
        self._serial_io.send_and_await_response("ATE1", response='OK')
        # activate displaying error as codes (mandatory)
        self._serial_io.send_and_await_response("AT+CMEE=1", response='OK')
        # activate displaying error as descriptions (optional)
        self._serial_io.send_and_await_response("AT+CMEE=2", response='OK')

    def close(self):
        """Close underlying serial connection."""
        if self.verbose:
            print("{}:{}  closing serial port {}".format(hostname, devname, self._serial_io.port))
        self._serial_io.close()
        print("{}  serial port {} closed".format(hostname, self._serial_io.port))

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # reraise exceptions if any

    def send(self, cmd):
        """Send data over underlying serial connection"""
        if self.verbose:
            print("{}:{}  sending AT command '{}'".format(hostname, devname, cmd))
        self._serial_io.send(cmd)


if __name__ == '__main__':
    import argparse

    def get_options():
        parser = argparse.ArgumentParser(description="Proxy AT console between serial port and stdin/stdout")
        parser.add_argument('serial_devname', help='serial device name like COM5, ttyS4')
        parser.add_argument('--verbose', action='store_true', help='show proxy internal processing')
        args = parser.parse_args()
        return args

    options = get_options()
    devname = options.serial_devname

    print("starting {} proxy at {} ...".format(devname, hostname))

    with AtConsoleProxy(port=options.serial_devname, verbose=options.verbose) as proxy:
        while True:
            cmd = input()
            if "exit_serial_proxy" in cmd:
                break
            try:
                proxy.send(cmd)
            except serial.SerialException as err:
                if options.verbose:
                    print("{}:{}  serial transmission of cmd '{}' failed: {!r}".format(hostname, devname, cmd, err))