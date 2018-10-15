from moler.config import load_config
from moler.device.device import DeviceFactory

load_config(path='my_devices.yml')                      # description of available devices
my_unix = DeviceFactory.get_device(name='MyMachine')    # take specific device out of available ones
ps_cmd = my_unix.get_cmd(cmd_name="ps",                 # take command of that device
                         cmd_params={"options": "-ef"})

processes_info = ps_cmd()                               # run the command, it returns result
for proc_info in processes_info:
    if 'python' in proc_info['CMD']:
        print("PID: {info[PID]} CMD: {info[CMD]}".format(info=proc_info))

"""
PID: 1817 CMD: /usr/bin/python /usr/share/system-config-printer/applet.py
PID: 21825 CMD: /usr/bin/python /home/gl/moler/examples/command/unix_ps.py
"""
