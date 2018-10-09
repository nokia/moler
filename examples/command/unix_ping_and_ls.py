from moler.config import load_config
from moler.device.device import DeviceFactory

load_config(path='my_devices.yml')

my_unix = DeviceFactory.get_device(name='MyMachine')
host = 'www.google.com'
ping_cmd = my_unix.get_cmd(cmd_name="ping", cmd_params={"destination": host, "options": "-w 6"})

remote_unix = DeviceFactory.get_device(name='RebexTestMachine')
remote_unix.goto_state(state="UNIX_REMOTE")
ls_cmd = remote_unix.get_cmd(cmd_name="ls", cmd_params={"options": "-l"})
ls_cmd.connection.newline = '\r\n'  # tweak since remote console uses such one

print("Start pinging {} ...".format(host))
ping_cmd.start()
print("Let's check readme.txt at {} while pinging {} ...".format(remote_unix.name, host))

remote_files = ls_cmd()
file_info = remote_files['files']['readme.txt']
print("readme.txt file: owner={fi[owner]}, size={fi[size_bytes]}".format(fi=file_info))

ping_stats = ping_cmd.await_done(timeout=6)
print("ping {}: {}={}, {}={} [{}]".format(host,'packet_loss',
                                          ping_stats['packet_loss'],
                                          'time_avg',
                                          ping_stats['time_avg'],
                                          ping_stats['time_unit']))

# result:
"""
readme.txt file:
  permissions       : -rw-------
  hard_links_count  : 1
  owner             : demo
  group             : users
  size_raw          : 403
  size_bytes        : 403
  date              : Apr 08  2014
  name              : readme.txt
"""
