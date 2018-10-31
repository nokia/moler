from moler.cmd.unix.ps import Ps
from moler.connection import ObservableConnection, get_connection
from moler.io.raw.terminal import ThreadedTerminal

# v.1 - combine all manually
# moler_conn = ObservableConnection()
# terminal = ThreadedTerminal(moler_connection=moler_conn)
# v.2 - let factory combine
terminal = get_connection(io_type='terminal', variant='threaded')
# v.3 - let factory select default variant
# terminal = get_connection(io_type='terminal')
terminal.open()
ps_cmd = Ps(connection=terminal.moler_connection, options="-ef")

processes = ps_cmd()
for proc in processes:
    if 'python' in proc['CMD']:
        print("PID: {} CMD: {}".format(proc['PID'], proc['CMD']))
terminal.close()

# result:
"""
PID: 1817 CMD: /usr/bin/python /usr/share/system-config-printer/applet.py
PID: 21825 CMD: /usr/bin/python /home/gl/moler/examples/command/unix_ps.py
"""
