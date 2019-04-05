import os.path
import time
from moler.config import load_config
from moler.device.device import DeviceFactory

load_config(config=os.path.abspath('my_devices.yml'))


my_r_unix = DeviceFactory.get_device(name='MyRemoteMachine')

iperf_options = "-c 127.0.0.1 -p 5001 -i 1 -t 5"
iperf_cmd = my_r_unix.get_cmd(cmd_name="iperf", cmd_params={"options": iperf_options})
print("step 1 of test")
processes = iperf_cmd.start()
print("step 2 of test")
time.sleep(3)           # some foreground action
print("----- test results ------")
iperf_result = iperf_cmd.await_done(timeout=4.2)
for conn in iperf_result['CONNECTIONS']:
    for iperf_record in iperf_result['CONNECTIONS'][conn]:
        print("{}: {}".format(iperf_record['Interval'], iperf_record['Transfer Raw']))
