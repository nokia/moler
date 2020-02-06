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


class SerialToStdout(serial.threaded.Protocol):
    """serial->stdout"""

    def __init__(self, prefix):
        self.prefix = prefix

    def __call__(self):
        return self

    def connection_made(self, transport):
        """Called when reader thread is started"""
        sys.stdout.write('{} opened\n'.format(self.prefix))

    def connection_lost(self, exc):
        """
        Called when the serial port is closed or the reader loop terminated
        otherwise.
        """
        if exc:
            sys.stdout.write('{} closed({!r})\n'.format(self.prefix, exc))
        else:
            sys.stdout.write('{} closed\n'.format(self.prefix))
        if isinstance(exc, Exception):
            raise exc

    def data_received(self, data):
        """Called with snippets received from the serial port"""
        sys.stdout.write(data)


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


class AtConsoleProxy(object):
    """Class to proxy AT commands console into stdin/stdout"""
    def __init__(self, port, verbose=False):
        self._serial_io = IOSerial(port=port)
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
        def echo_by_print(msg):
            print(msg)

        # activate echo of AT commands
        self.send_and_echo_response("ATE1", echo_function=echo_by_print)
        # activate displaying error as codes (mandatory)
        self.send_and_echo_response("AT+CMEE=1", echo_function=echo_by_print)
        # activate displaying error as descriptions (optional)
        self.send_and_echo_response("AT+CMEE=2", echo_function=echo_by_print)

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

    def send_and_echo_response(self, cmd, echo_function, timeout=4):
        """Send data, await response and echo it"""
        self.send(cmd)
        resp = self.await_response(timeout=timeout)
        for line in resp:
            echo_function(line)

    def read(self):
        """Returns subsequent lines read from underlying serial connection"""
        out_data = self._serial_io.read()
        out_lines = out_data.splitlines()
        if self.verbose:
            print("{}:{}  read serial port output: {}".format(hostname, devname, out_lines))
        return out_lines

    def await_response(self, timeout=4.0):
        """Returns subsequent lines read from serial connection within timeout"""
        out_lines = []
        if self.verbose:
            print("{}:{}  awaiting {} sec for serial port response".format(hostname, devname, timeout))
        start_time = time.time()
        for line in self.read():
            read_duration = time.time() - start_time
            if line:
                out_lines.append(line)
                self.check_for_timeout(read_duration, timeout, out_lines)
                self.validate_no_at_error(out_lines)
                if self.is_at_output_complete(out_lines):
                    if self.verbose:
                        print("{}:{}  complete AT response received after {} sec".format(hostname, devname, read_duration))
                    return out_lines
            else:
                self.check_for_timeout(read_duration, timeout, out_lines)
            time.sleep(0.05)

    @staticmethod
    def validate_no_at_error(output_lines):
        """Check if output is not failed AT command"""
        if "ERROR" in output_lines:
            raise serial.SerialException("Response: {}".format(output_lines))

    @staticmethod
    def is_at_output_complete(output_lines):
        """Check if output is complete AT command output (finished by OK)"""
        return "OK" in output_lines

    @staticmethod
    def check_for_timeout(duration, timeout, output_lines):
        """Check if we have exceeded timeout"""
        if duration > timeout:
            timeout_str = "took {} > {} sec timeout".format(duration, timeout)
            err_str = "Awaiting serial response {}. Received: {}".format(timeout_str, output_lines)
            raise serial.SerialException(err_str)


class AtToStdout(serial.threaded.LineReader):
    """ATserial->stdout"""

    def __init__(self, prefix):
        super(AtToStdout, self).__init__()
        self.prefix = prefix
        self.awaited_output = None
        self._collect = threading.Event()
        self._data_access = threading.Lock()
        self._collected_data = ''
        self._await = threading.Event()
        self._found = threading.Event()

    def __call__(self):
        return self

    def connection_made(self, transport):
        sys.stdout.write('{} >>> opened\n'.format(self.prefix))
        super(AtToStdout, self).connection_made(transport)
        msg = "{}:{}  opened".format(hostname, transport)
        sys.stdout.write('{}\n'.format(msg))

    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)
        msg = "{}:{}  closed".format(hostname, self.transport)
        sys.stdout.write('{}\n'.format(msg))

    def handle_line(self, data):
        sys.stdout.write('line received: {!r}\n'.format(data))
        sys.stdout.write(data.encode(self.ENCODING, self.UNICODE_HANDLING) + b'\n')
        print(data)

    def write_line(self, text):
        sys.stdout.write('sending line: {!r}\n'.format(text))
        super(AtToStdout, self).write_line(text)

    def data_received(self, data):
        """Called with snippets received from the serial port"""
        # operates inside "reader thread"
        sys.stdout.write('data received: {!r}\n'.format(data))
        super(AtToStdout, self).data_received(data)
    #     if self._collect.is_set():
    #         with self._data_access:
    #             self._collected_data = self._collected_data + data
    #             if self._await.is_set():
    #                 if self.awaited_output in self._collected_data:
    #                     self._found.set()

    @contextmanager
    def _collect_output(self):
        try:
            self._collect.set()
            yield
        finally:
            self._collect.clear()
            with self._data_access:
                self._collected_data = ''

    @contextmanager
    def send_and_await_response(self, data, timeout):
        """Await till data comes"""
        # to be used in "sender thread"
        with self._collect_output():
            try:
                yield  # here client code will do AT send
                self.awaited_output = data
                self._found.clear()
                self._await.set()
            finally:
                self.awaited_output = None


class AtConsoleProxy2(object):
    """Class to proxy AT commands console into stdin/stdout"""
    def __init__(self, port, verbose=False):
        ser_to_stdout = SerialToStdout("{}:{}  port".format(hostname, port))
        ser_to_stdout = AtToStdout("{}:{}  port".format(hostname, port))
        self._serial_io = IoThreadedSerial(port=port, protocol_factory=ser_to_stdout)
        self.verbose = verbose

    def open(self):
        """
        Open underlying serial connection.

        Return context manager to allow for:  with connection.open() as conn:
        """
        print("{}  opening serial port {}".format(hostname, self._serial_io.port))
        self._serial_io.open()

        return self

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
        # self._serial_io.send(cmd)
        self._serial_io.protocol.write_line(cmd)


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
    # with AtConsoleProxy(port=options.serial_devname, verbose=options.verbose) as proxy:
    #     while True:
    #         cmd = raw_input("{}:{}> ".format(hostname, devname))
    #         if "exit_serial_proxy" in cmd:
    #             break
    #         try:
    #             proxy.send(cmd)
    #             resp = proxy.await_response(timeout=4)
    #             for line in resp:
    #                 print(line)
    #         except serial.SerialException as err:
    #             if options.verbose:
    #                 print("{}:{}  serial transmission of cmd '{}' failed: {!r}".format(hostname, devname, cmd, err))
    with AtConsoleProxy2(port=options.serial_devname, verbose=options.verbose) as proxy:
        while True:
            cmd = input()
            if "exit_serial_proxy" in cmd:
                break
            try:
                proxy.send(cmd)
            except serial.SerialException as err:
                if options.verbose:
                    print("{}:{}  serial transmission of cmd '{}' failed: {!r}".format(hostname, devname, cmd, err))

# TODO: remove newlines from proxy responsibility.
