# -*- coding: utf-8 -*-
"""
Moler example on local host Unix PC.
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'michal.ernst@nokia.com'


from moler.config import load_config
from moler.device.device import DeviceFactory
from moler.util.moler_test import MolerTest
import time


class Test_example():

    @MolerTest.raise_background_exceptions(check_steps_end=True)
    def test_case_1(self, expected_time=5):
        MolerTest.info("Load configuration from configuration file.")
        load_config(config="/home/ute/auto/workshop20190211/training_config.yml")

        MolerTest.info("Get and prepare all devices.")

        unix_1 = DeviceFactory.get_device("UNIX_1")
        unix_2 = DeviceFactory.get_device("UNIX_2")
        unix_1.goto_state("UNIX_LOCAL")
        unix_2.goto_state("UNIX_LOCAL")

        MolerTest.info("Prepare event for ping response.")
        ping_response_event = unix_1.get_event(
            event_name="ping_response",
            event_params={}
        )
        MolerTest.info("Prepare event for ping no response.")
        ping_no_response_event = unix_1.get_event(
            event_name="ping_no_response",
            event_params={}
        )

        times = {
            "connection_lost": None,
            "reconnect": None,
        }

        MolerTest.info("Add callback to ping response event.")
        ping_response_event.add_event_occurred_callback(
            callback=self.ping_response_callback,
            callback_params={
                "msg": "CALLBACK PING_RESPONSE",
                "event": ping_response_event,
                "times": times
            }
        )
        MolerTest.info("Add callback to ping no response event.")
        ping_no_response_event.add_event_occurred_callback(
            callback=self.ping_no_response_callback,
            callback_params={
                "msg": "CALLBACK PING_NO_RESPONSE",
                "event": ping_no_response_event,
                "times": times
            }
        )

        MolerTest.info("Start both events.")
        ping_response_event.start()
        ping_no_response_event.start()

        MolerTest.info("Get ping command.")
        ping_cmd = unix_1.get_cmd(
            cmd_name="ping",
            cmd_params={
                'destination': 'localhost',
                'options': '-O'
            }
        )

        MolerTest.info("Start ping command in background.")
        ping_cmd.start(timeout=1500)

        MolerTest.info("Prepare ifconfig command object to execute it as root and simulate connection lost.")
        ifconfig_lo_down_cmd = unix_2.get_cmd(
            cmd_name="ifconfig",
            cmd_params={
                "options": "lo down"
            }
        )

        MolerTest.info("Execute ifconfig command as superuser using sudo command.")
        sudo_cmd = unix_2.get_cmd(
            cmd_name="sudo",
            cmd_params={
                'password': 'ute',
                'cmd_object': ifconfig_lo_down_cmd
            }
        )
        result = sudo_cmd()

        MolerTest.sleep(seconds=3)

        MolerTest.info("Prepare ifconfig command object to execute it as root and simulate reconnect.")
        ifconfig_lo_up_cmd = unix_2.get_cmd(
            cmd_name="ifconfig",
            cmd_params={
                "options": "lo up"
            }
        )

        MolerTest.info("Execute ifconfig command as superuser using sudo command.")
        sudo_cmd = unix_2.get_cmd(
            cmd_name="sudo",
            cmd_params={
                'password': 'ute',
                'cmd_object': ifconfig_lo_up_cmd
            }
        )
        result = sudo_cmd()

        MolerTest.sleep(seconds=5)

        MolerTest.info("Break ping command and stop all events.")
        ping_cmd.cancel()
        ping_response_event.cancel()
        ping_no_response_event.cancel()

        delta_time = times["reconnect"] - times["connection_lost"]

        if delta_time > 0 and delta_time <= expected_time:
            MolerTest.info("Reconection time was '{} s' so lower than '{} s' as expected.".format(
                delta_time,
                expected_time
            ))
        else:
            MolerTest.error("Too long reconnection time! Expected: '{} s' but got '{} s'".format(
                expected_time,
                delta_time,
            ))

        MolerTest.steps_end()

    def ping_response_callback(self, msg, event, times):
        MolerTest.info(msg)
        MolerTest.info(event._occurred[-1])
        if times["connection_lost"]:
            if not times["reconnect"]:
                times["reconnect"] = time.time()

    def ping_no_response_callback(self, msg, event, times):
        MolerTest.info(msg)
        MolerTest.info(event._occurred[-1])
        if not times["connection_lost"]:
            times["connection_lost"] = time.time()
