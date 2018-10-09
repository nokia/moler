from moler.config import load_config
from moler.device.device import DeviceFactory

load_config(path='my_devices.yml')
my_unix = DeviceFactory.get_device(name='MyMachine')
ps_cmd = my_unix.get_cmd(cmd_name="ps", cmd_params={"options": "-ef"})

processes = ps_cmd()
for proc in processes:
    if 'python' in proc['CMD']:
        print("PID: {} CMD: {}".format(proc['PID'], proc['CMD']))

"""
PID: 1817 CMD: /usr/bin/python /usr/share/system-config-printer/applet.py
PID: 21825 CMD: /usr/bin/python /home/gl/moler/examples/command/unix_ps.py
"""
