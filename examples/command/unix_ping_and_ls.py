from moler.config import load_config
from moler.device.device import DeviceFactory

load_config(config='my_devices.yml')

my_unix = DeviceFactory.get_device(name='MyMachine')
host = 'www.google.com'
ping_cmd = my_unix.get_cmd(cmd_name="ping", cmd_params={"destination": host, "options": "-w 6"})

remote_unix = DeviceFactory.get_device(name='RebexTestMachine')
remote_unix.goto_state(state="UNIX_REMOTE")
ls_cmd = remote_unix.get_cmd(cmd_name="ls", cmd_params={"options": "-l"})

print("Start pinging {} ...".format(host))
ping_cmd.start()                                # run command in background
print("Let's check readme.txt at {} while pinging {} ...".format(remote_unix.name, host))

remote_files = ls_cmd()                         # foreground "run in the meantime"
file_info = remote_files['files']['readme.txt']
print("readme.txt file: owner={fi[owner]}, size={fi[size_bytes]}".format(fi=file_info))

ping_stats = ping_cmd.await_done(timeout=6)     # await background command
print("ping {}: {}={}, {}={} [{}]".format(host,'packet_loss',
                                          ping_stats['packet_loss'],
                                          'time_avg',
                                          ping_stats['time_avg'],
                                          ping_stats['time_unit']))

# result:
"""
Start pinging www.google.com ...
Let's check readme.txt at RebexTestMachine while pinging www.google.com ...
readme.txt file: owner=demo, size=403
ping www.google.com: packet_loss=0, time_avg=49.686 [ms]
"""
