import os.path
from moler.config import load_config
from moler.device.device import DeviceFactory

load_config(config=os.path.abspath('my_devices.yml'))


my_r_unix = DeviceFactory.get_device(name='MyRemoteMachine')

ps_cmd = my_r_unix.get_cmd(cmd_name="ps", cmd_params={"options": "-ef"})

processes = ps_cmd()

for proc in processes:
    if "python" in proc["CMD"]:
        print("PID: {} CMD: {}".format(proc["PID"], proc["CMD"]))
