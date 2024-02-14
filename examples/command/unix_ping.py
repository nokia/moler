import time
from moler.cmd.unix.ping import Ping
from moler.connection_factory import get_connection

host = 'www.google.com'
terminal = get_connection(io_type='terminal', variant='threaded')
with terminal.open():
    ping_cmd = Ping(connection=terminal.moler_connection,
                    destination=host, options="-w 6")
    print(f"Start pinging {host} ...")
    ping_cmd.start()
    print(f"Doing other stuff while pinging {host} ...")
    time.sleep(3)
    ping_stats = ping_cmd.await_done(timeout=4)
    print("ping {}: {}={}, {}={} [{}]".format(host,'packet_loss',
                                              ping_stats['packet_loss'],
                                              'time_avg',
                                              ping_stats['time_avg'],
                                              ping_stats['time_unit']))
# result:
"""
Start pinging www.google.com ...
Doing other stuff while pinging www.google.com ...
ping www.google.com: packet_loss=0, time_avg=50.000 [ms]
"""
