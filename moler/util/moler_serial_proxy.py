import serial
import time
import contextlib


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
        print("opening serial port {}".format(self.port))
        self._serial_connection = serial.Serial(port=self.port,
                                                baudrate=self.baudrate,
                                                stopbits=self.stopbits,
                                                parity=self.parity,
                                                timeout=self.timeout,
                                                xonxoff=self.xonxoff)
        return contextlib.closing(self)

    def close(self):
        """Close established connection."""
        print("closing serial port {}".format(self.port))
        self._serial_connection.close()
        print("serial port {} closed".format(self.port))

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # reraise exceptions if any

    def send(self, cmd):
        """Sends data over serial connection"""
        print("sending AT command '{}'".format(cmd))
        self._serial_connection.write("{}\r\n".format(cmd))
        self._serial_connection.flush()

    def read(self):
        """Returns subsequent lines read from serial connection"""
        lines = self._serial_connection.readlines()
        out_lines = [ln.strip('\r\n') for ln in lines]
        print("read serial port output: {}".format(out_lines))
        return out_lines


class AtConsoleProxy(object):
    """Class to proxy AT commands console into stdin/stdout"""
    def __init__(self, port):
        self._serial_io = IOSerial(port=port)

    def open(self):
        """
        Open underlying serial connection.

        Return context manager to allow for:  with connection.open() as conn:
        """
        self._serial_io.open()
        return contextlib.closing(self)

    def close(self):
        """Close underlying serial connection."""
        self._serial_io.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # reraise exceptions if any

    def send(self, cmd):
        """Send data over underlying serial connection"""
        self._serial_io.send(cmd)

    def read(self):
        """Returns subsequent lines read from underlying serial connection"""
        out_lines = self._serial_io.read()
        return out_lines

    def await_response(self, timeout=4.0):
        """Returns generator object providing subsequent lines read from serial connection within timeout"""
        out_lines = []
        print("awaiting {} sec for serial port response".format(timeout))
        start_time = time.time()
        for line in self.read():
            read_duration = time.time() - start_time
            if line:
                out_lines.append(line)
                self.check_for_timeout(read_duration, timeout, out_lines)
                self.validate_no_at_error(out_lines)
                if self.is_at_output_complete(out_lines):
                    print("serial response received after {} sec".format(read_duration))
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
    with AtConsoleProxy(port="COM5") as proxy:
        cmd = "AT"
        try:
            proxy.send(cmd)
            resp = proxy.await_response(timeout=4)
            print("serial transmission of cmd '{}' returned: {}".format(cmd, resp))
        except serial.SerialException as err:
            print("serial transmission of cmd '{}' failed: {!r}".format(cmd, err))
