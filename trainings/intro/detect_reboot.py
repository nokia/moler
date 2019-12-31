import os.path
import time
from moler.config import load_config
from moler.device.device import DeviceFactory
from moler.util.moler_test import MolerTest

load_config(config=os.path.abspath('my_devices.yml'))


def rebooting_callback():
    msg = "Machine is rebooting in background !!!"
    print(msg)
    MolerTest.info(msg)


my_r_unix = DeviceFactory.get_device(name='MyRemoteMachine')
shutdown_ev = my_r_unix.get_event(event_name="shutdown")
shutdown_ev.add_event_occurred_callback(callback=rebooting_callback,
                                        callback_params={})
shutdown_ev.start()
print("step 1 of test")
time.sleep(2)
print("step 2 of test")
time.sleep(8)
print("end of test")
