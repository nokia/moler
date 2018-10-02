from moler.cmd.unix.ps import Ps
from moler.connection import ObservableConnection
from moler.io.raw.terminal import ThreadedTerminal

moler_conn = ObservableConnection()
terminal = ThreadedTerminal(moler_connection=moler_conn)
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
PID: 21825 CMD: /opt/ute/python3/bin/python3 /home/ute/auto/moler/moler/examples/command/unix_ps.py
"""
