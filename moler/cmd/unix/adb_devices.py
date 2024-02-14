"""
Module for command adb devices.
"""

__author__ = "Marcin Usielski"
__copyright__ = "Copyright (C) 2022, Nokia"
__email__ = "marcin.usielski@nokia.com"


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class AdbDevices(GenericUnixCommand):
    def __init__(
        self,
        connection=None,
        prompt=None,
        newline_chars=None,
        runner=None,
        options=None,
    ):
        """
        Create instance of adb devices class.
        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(AdbDevices, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.options = options
        self.ret_required = False
        self.current_ret["DEVICES"] = {}

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = (
            "adb devices" if not self.options else f"adb devices {self.options}"
        )
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._ignore_line(line)
                self._device_more_elements(line)
                self._device_2_elements(line)
            except ParsingDone:
                pass
        super(AdbDevices, self).on_new_line(line=line, is_full_line=is_full_line)

    # List of devices attached
    _re_ignore = re.compile(r"^\s*List of devices attached")

    def _ignore_line(self, line):
        if self._regex_helper.search_compiled(AdbDevices._re_ignore, line):
            raise ParsingDone()

    # emulator-5554 device
    _re_2_elements = re.compile(r"(?P<NAME>\S+)\s+(?P<TYPE>\S+)")

    def _device_2_elements(self, line):
        if self._regex_helper.search_compiled(AdbDevices._re_2_elements, line):
            name = self._regex_helper.group("NAME")
            kind = self._regex_helper.group("TYPE")
            self.current_ret["DEVICES"][name] = {}
            self.current_ret["DEVICES"][name]["NAME"] = name
            self.current_ret["DEVICES"][name]["TYPE"] = kind
            raise ParsingDone()

    # emulator-5556 device product:sdk_google_phone_x86_64 model:Android_SDK_built_for_x86_64 device:generic_x86_64
    _re_more_elements = re.compile(r"(?P<NAME>\S+)\s+(?P<TYPE>\S+)\s+(?P<RAW>\S.*\S)")

    def _device_more_elements(self, line):
        if self._regex_helper.search_compiled(AdbDevices._re_more_elements, line):
            name = self._regex_helper.group("NAME")
            kind = self._regex_helper.group("TYPE")
            raw = self._regex_helper.group("RAW")
            self.current_ret["DEVICES"][name] = {}
            self.current_ret["DEVICES"][name]["DETAILS"] = {}
            self.current_ret["DEVICES"][name]["NAME"] = name
            self.current_ret["DEVICES"][name]["TYPE"] = kind
            self.current_ret["DEVICES"][name]["DETAILS"]["raw"] = raw
            for subelement in raw.split():
                token_name, token_value = subelement.split(":")
                self.current_ret["DEVICES"][name]["DETAILS"][token_name] = token_value
            raise ParsingDone()


COMMAND_OUTPUT = """adb devices
List of devices attached
emulator-4357 device
$"""

COMMAND_RESULT = {
    "DEVICES": {
        "emulator-4357": {
            "NAME": "emulator-4357",
            "TYPE": "device",
        }
    },
}

COMMAND_KWARGS = {}


COMMAND_OUTPUT_more = """adb devices
List of devices attached
emulator-4356 device product:sdk_google_phone_x86_64 model:Android_SDK_built_for_x86_64 device:generic_x86_64
$"""

COMMAND_RESULT_more = {
    "DEVICES": {
        "emulator-4356": {
            "NAME": "emulator-4356",
            "TYPE": "device",
            "DETAILS": {
                "raw": "product:sdk_google_phone_x86_64 model:Android_SDK_built_for_x86_64 device:generic_x86_64",
                "product": "sdk_google_phone_x86_64",
                "model": "Android_SDK_built_for_x86_64",
                "device": "generic_x86_64",
            },
        }
    },
}

COMMAND_KWARGS_more = {}
