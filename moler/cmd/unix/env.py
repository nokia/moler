# -*- coding: utf-8 -*-
"""
Env command module.
"""

__author__ = 'Haili Guo'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'haili.guo@nokia-sbell.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Env(GenericUnixCommand):

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        super(Env, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.ret_required = True

    def build_command_string(self):
        cmd = "env"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_name_line(line)
            except ParsingDone:
                pass
        return super(Env, self).on_new_line(line, is_full_line)

    _re_name_line = re.compile(r"^(?P<title>\S+)=(?P<content>.*)$")

    def _parse_name_line(self, line):
        if self._regex_helper.search_compiled(Env._re_name_line, line):
            name = self._regex_helper.group("title")
            self.current_ret[name] = self._regex_helper.group("content")
            raise ParsingDone


COMMAND_OUTPUT = """
host:~# env
LESSKEY=/etc/lesskey.bin
NNTPSERVER=news
MANPATH=/usr/share/man:/usr/local/man:/usr/local/share/man
XDG_SESSION_ID=26352
HOSTNAME=FZM-TDD-249
XKEYSYMDB=/usr/X11R6/lib/X11/XKeysymDB
HOST=FZM-TDD-249
TERM=xterm-mono
SHELL=/bin/bash
PROFILEREAD=true
HISTSIZE=1000
SSH_CLIENT=10.83.200.37 40356 22
MORE=-sl
OLDPWD=/root
SSH_TTY=/dev/pts/3
NO_PROXY=localhost, 127.0.0.1, 192.168.0.0/16, 10.83.0.0/16, 10.254.0.0/16, 10.0.0.0/16
http_proxy=http://87.254.212.120:8080
JRE_HOME=/usr/lib64/jvm/jre-1.7.0
USER=root
LS_COLORS=
XNLSPATH=/usr/share/X11/nls
QEMU_AUDIO_DRV=pa
HOSTTYPE=x86_64
ftp_proxy=http://87.254.212.120:8080
CONFIG_SITE=/usr/share/site/x86_64-unknown-linux-gnu
FROM_HEADER=
PAGER=less
CSHEDIT=emacs
XDG_CONFIG_DIRS=/etc/xdg
LIBGL_DEBUG=quiet
MINICOM=-c on
MAIL=/var/mail/root
PATH=/sbin:/usr/sbin:/usr/local/sbin:/root/bin:/usr/local/bin:/usr/bin:/bin:/usr/bin/X11:/usr/games:/usr/lib/mit/bin:/usr/lib/mit/sbin:/home/emssim/lte1702/bin/shared/
CPU=x86_64
JAVA_BINDIR=/usr/java/latest/bin
SSH_SENDS_LOCALE=yes
INPUTRC=/etc/inputrc
PWD=/l
gopher_proxy=
JAVA_HOME=/usr/java/latest
LANG=en_US.UTF-8
PYTHONSTARTUP=/etc/pythonstart
https_proxy=http://87.254.212.120:8080
GPG_TTY=/dev/pts/3
AUDIODRIVER=pulseaudio
QT_SYSTEM_DIR=/usr/share/desktop-data
SHLVL=1
HOME=/root
ALSA_CONFIG_PATH=/etc/alsa-pulse.conf
SDL_AUDIODRIVER=pulse
LESS_ADVANCED_PREPROCESSOR=no
OSTYPE=linux
LS_OPTIONS=-A -N --color=none -T 0
no_proxy=localhost, 127.0.0.1, 192.168.0.0/16, 10.83.0.0/16, 10.254.0.0/16, 10.0.0.0/16
XCURSOR_THEME=DMZ
WINDOWMANAGER=/usr/bin/kde4
G_FILENAME_ENCODING=@locale,UTF-8,ISO-8859-15,CP1252
LESS=-M -I -R
MACHTYPE=x86_64-suse-linux
LOGNAME=root
CVS_RSH=ssh
XDG_DATA_DIRS=/usr/share
SSH_CONNECTION=10.83.200.37 40356 10.83.205.103 22
LESSOPEN=lessopen.sh %s
XDG_RUNTIME_DIR=/run/user/0
BTS_SITE_MANAGER_INSTALL_PATH=/opt/NSN/Managers/BTS Site/BTS Site Manager
VDPAU_DRIVER=va_gl
NO_AT_BRIDGE=1
LESSCLOSE=lessclose.sh %s %s
G_BROKEN_FILENAMES=1
JAVA_ROOT=/usr/java/latest
COLORTERM=1
BASH_FUNC_mc%%=() {  . /usr/share/mc/mc-wrapper.sh
_=/usr/bin/env
host:~#"""

COMMAND_RESULT = {
    'ALSA_CONFIG_PATH': '/etc/alsa-pulse.conf',
    'AUDIODRIVER': 'pulseaudio',
    'BASH_FUNC_mc%%': '() {  . /usr/share/mc/mc-wrapper.sh',
    'BTS_SITE_MANAGER_INSTALL_PATH': '/opt/NSN/Managers/BTS Site/BTS Site Manager',
    'COLORTERM': '1',
    'CONFIG_SITE': '/usr/share/site/x86_64-unknown-linux-gnu',
    'CPU': 'x86_64',
    'CSHEDIT': 'emacs',
    'CVS_RSH': 'ssh',
    'FROM_HEADER': '',
    'GPG_TTY': '/dev/pts/3',
    'G_BROKEN_FILENAMES': '1',
    'G_FILENAME_ENCODING': '@locale,UTF-8,ISO-8859-15,CP1252',
    'HISTSIZE': '1000',
    'HOME': '/root',
    'HOST': 'FZM-TDD-249',
    'HOSTNAME': 'FZM-TDD-249',
    'HOSTTYPE': 'x86_64',
    'INPUTRC': '/etc/inputrc',
    'JAVA_BINDIR': '/usr/java/latest/bin',
    'JAVA_HOME': '/usr/java/latest',
    'JAVA_ROOT': '/usr/java/latest',
    'JRE_HOME': '/usr/lib64/jvm/jre-1.7.0',
    'LANG': 'en_US.UTF-8',
    'LESS': '-M -I -R',
    'LESSCLOSE': 'lessclose.sh %s %s',
    'LESSKEY': '/etc/lesskey.bin',
    'LESSOPEN': 'lessopen.sh %s',
    'LESS_ADVANCED_PREPROCESSOR': 'no',
    'LIBGL_DEBUG': 'quiet',
    'LOGNAME': 'root',
    'LS_COLORS': '',
    'LS_OPTIONS': '-A -N --color=none -T 0',
    'MACHTYPE': 'x86_64-suse-linux',
    'MAIL': '/var/mail/root',
    'MANPATH': '/usr/share/man:/usr/local/man:/usr/local/share/man',
    'MINICOM': '-c on',
    'MORE': '-sl',
    'NNTPSERVER': 'news',
    'NO_AT_BRIDGE': '1',
    'NO_PROXY': 'localhost, 127.0.0.1, 192.168.0.0/16, 10.83.0.0/16, 10.254.0.0/16, 10.0.0.0/16',
    'OLDPWD': '/root',
    'OSTYPE': 'linux',
    'PAGER': 'less',
    'PATH': '/sbin:/usr/sbin:/usr/local/sbin:/root/bin:/usr/local/bin:/usr/bin:/bin:/usr/bin/X11:/usr/games:/usr/lib/mit/bin:/usr/lib/mit/sbin:/home/emssim/lte1702/bin/shared/',
    'PROFILEREAD': 'true',
    'PWD': '/l',
    'PYTHONSTARTUP': '/etc/pythonstart',
    'QEMU_AUDIO_DRV': 'pa',
    'QT_SYSTEM_DIR': '/usr/share/desktop-data',
    'SDL_AUDIODRIVER': 'pulse',
    'SHELL': '/bin/bash',
    'SHLVL': '1',
    'SSH_CLIENT': '10.83.200.37 40356 22',
    'SSH_CONNECTION': '10.83.200.37 40356 10.83.205.103 22',
    'SSH_SENDS_LOCALE': 'yes',
    'SSH_TTY': '/dev/pts/3',
    'TERM': 'xterm-mono',
    'USER': 'root',
    'VDPAU_DRIVER': 'va_gl',
    'WINDOWMANAGER': '/usr/bin/kde4',
    'XCURSOR_THEME': 'DMZ',
    'XDG_CONFIG_DIRS': '/etc/xdg',
    'XDG_DATA_DIRS': '/usr/share',
    'XDG_RUNTIME_DIR': '/run/user/0',
    'XDG_SESSION_ID': '26352',
    'XKEYSYMDB': '/usr/X11R6/lib/X11/XKeysymDB',
    'XNLSPATH': '/usr/share/X11/nls',
    '_': '/usr/bin/env',
    'ftp_proxy': 'http://87.254.212.120:8080',
    'gopher_proxy': '',
    'http_proxy': 'http://87.254.212.120:8080',
    'https_proxy': 'http://87.254.212.120:8080',
    'no_proxy': 'localhost, 127.0.0.1, 192.168.0.0/16, 10.83.0.0/16, 10.254.0.0/16, 10.0.0.0/16'
}

COMMAND_KWARGS = {}
