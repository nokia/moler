import serial
import time
import contextlib
import platform

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
        return contextlib.closing(self)

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
        self._serial_connection.write("{}\r\n".format(cmd))
        self._serial_connection.flush()

    def read(self):
        """Returns subsequent lines read from serial connection"""
        lines = self._serial_connection.readlines()
        out_lines = [ln.strip('\r\n') for ln in lines]
        return out_lines


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
        self.send("ATE1")  # activate echo of AT commands
        return contextlib.closing(self)

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

    def read(self):
        """Returns subsequent lines read from underlying serial connection"""
        out_lines = self._serial_io.read()
        if self.verbose:
            print("{}:{}  read serial port output: {}".format(hostname, devname, out_lines))
        return out_lines

    def await_response(self, timeout=4.0):
        """Returns generator object providing subsequent lines read from serial connection within timeout"""
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
        echo_resp = proxy.await_response(timeout=4)
        for line in echo_resp:
            print(line)
        while True:
            cmd = raw_input("{}:{}> ".format(hostname, devname))
            if "exit_serial_proxy" in cmd:
                break
            try:
                proxy.send(cmd)
                resp = proxy.await_response(timeout=4)
                for line in resp:
                    print(line)
            except serial.SerialException as err:
                if options.verbose:
                    print("{}:{}  serial transmission of cmd '{}' failed: {!r}".format(hostname, devname, cmd, err))


# TODO: remove newlines from io/proxy responsibility.
