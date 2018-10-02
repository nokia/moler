from moler.cmd.unix.ping import Ping
from moler.connection import ObservableConnection
from moler.io.raw.terminal import ThreadedTerminal

moler_conn = ObservableConnection()
terminal = ThreadedTerminal(moler_connection=moler_conn)
terminal.open()
ping_cmd = Ping(connection=terminal.moler_connection, destination='www.google.com', options="-w 6")
print(ping_cmd())
terminal.close()
