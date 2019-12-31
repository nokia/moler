import os.path
from moler.config import load_config
from moler.device.device import DeviceFactory

load_config(config=os.path.abspath('my_devices.yml'))

my_r_unix = DeviceFactory.get_device(name='MyRemoteMachine')

print(my_r_unix)

