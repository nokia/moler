# -*- coding: utf-8 -*-
"""
Export command module.
"""

__author__ = 'Yang Snackwell'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'snackwell.yang@nokia-sbell.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Export(GenericUnixCommand):

    def __init__(self, connection, prompt=None, newline_chars=None, ps1_param=None, set_param=None, runner=None):
        super(Export, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        if ps1_param or set_param:
            self.ret_required = False
        else:
            self.ret_required = True
        self.ps1 = ps1_param
        self.set = set_param

    def build_command_string(self):
        cmd = "export"
        if self.ps1:
            cmd = f"{cmd} PS1={self.ps1}"
        elif self.set:
            cmd = f"{cmd} {self.set}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_export_line(line)
            except ParsingDone:
                pass
        return super(Export, self).on_new_line(line, is_full_line)

    _re_export_line = re.compile(r"declare\s-x\s(?P<name>\S+)=\"(?P<value>.*)\"")

    def _parse_export_line(self, line):
        if self._regex_helper.search_compiled(self._re_export_line, line):
            name = self._regex_helper.group("name")
            self.current_ret[name] = self._regex_helper.group("value").replace("\\", "\\\\")
            raise ParsingDone


COMMAND_OUTPUT = """
[root@AP-AWT-LP3-11: ~]$ export
declare -x ALSA_CONFIG_PATH="/etc/alsa-pulse.conf"
declare -x COLORTERM="1"
declare -x CPU="i686"
declare -x CSHEDIT="emacs"
declare -x CVS_RSH="ssh"
declare -x FROM_HEADER=""
declare -x GPG_TTY="/dev/pts/12"
declare -x G_BROKEN_FILENAMES="1"
declare -x G_FILENAME_ENCODING
declare -x HISTSIZE="1000"
declare -x HOME="/root"
declare -x HOST="AP-AWT-LP3-11"
declare -x HOSTNAME="AP-AWT-LP3-11"
declare -x HOSTTYPE="i386"
declare -x INPUTRC="/etc/inputrc"
declare -x JAVA_BINDIR="/usr/lib/jvm/java/bin"
declare -x JAVA_HOME="/usr/lib/jvm/java"
declare -x JAVA_ROOT="/usr/lib/jvm/java"
declare -x JDK_HOME="/usr/lib/jvm/java"
declare -x JRE_HOME="/usr/lib/jvm/jre"
declare -x LANG="POSIX"
declare -x LC_CTYPE="en_US.UTF-8"
declare -x LESS="-M -I -R"
declare -x LESSCLOSE="lessclose.sh %s %s"
declare -x LESSKEY="/etc/lesskey.bin"
declare -x LESSOPEN="lessopen.sh %s"
declare -x LESS_ADVANCED_PREPROCESSOR="no"
declare -x LOGNAME="root"
declare -x MACHTYPE="i686-suse-linux"
declare -x MAIL="/var/mail/root"
declare -x MANPATH="/usr/share/man:/usr/local/man"
declare -x MINICOM="-c on"
declare -x MORE="-sl"
declare -x NNTPSERVER="news"
declare -x NO_PROXY="localhost, 127.0.0.1"
declare -x OLDPWD
declare -x OSTYPE="linux"
declare -x PAGER="less"
declare -x PATH="/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin:/usr/bin/X11:/usr/X11R6/bin:/usr/games"
declare -rx PROFILEREAD="true"
declare -x PS1="[\\u@\\h: \\w]\\$ "
declare -x PWD="/root"
declare -x PYTHONSTARTUP="/etc/pythonstart"
declare -x QT_SYSTEM_DIR="/usr/share/desktop-data"
declare -x SDK_HOME="/usr/lib/jvm/java"
declare -x SDL_AUDIODRIVER="pulse"
declare -x SHELL="/bin/bash"
declare -x SHLVL="1"
declare -x SSH_CLIENT="10.83.202.135 54079 22"
declare -x SSH_CONNECTION="10.83.202.135 54079 10.83.202.135 22"
declare -x SSH_SENDS_LOCALE="yes"
declare -x SSH_TTY="/dev/pts/12"
declare -x TERM="xterm"
declare -x USER="root"
declare -x WINDOWMANAGER="/usr/bin/gnome"
declare -x XCURSOR_THEME="DMZ"
declare -x XDG_CONFIG_DIRS="/etc/xdg"
declare -x XDG_DATA_DIRS="/usr/share"
declare -x XKEYSYMDB="/usr/X11R6/lib/X11/XKeysymDB"
declare -x XNLSPATH="/usr/share/X11/nls"
declare -x ftp_proxy="http://10.159.224.230:8080"
declare -x http_proxy="http://10.159.224.230:8080"
declare -x https_proxy="http://10.159.224.230:8080"
declare -x no_proxy="localhost, 127.0.0.1"
[root@AP-AWT-LP3-11: ~]$ """

COMMAND_RESULT = {
    'ALSA_CONFIG_PATH': '/etc/alsa-pulse.conf',
    'COLORTERM': '1',
    'CPU': 'i686',
    'CSHEDIT': 'emacs',
    'CVS_RSH': 'ssh',
    'FROM_HEADER': '',
    'GPG_TTY': '/dev/pts/12',
    'G_BROKEN_FILENAMES': '1',
    'HISTSIZE': '1000',
    'HOME': '/root',
    'HOST': 'AP-AWT-LP3-11',
    'HOSTNAME': 'AP-AWT-LP3-11',
    'HOSTTYPE': 'i386',
    'INPUTRC': '/etc/inputrc',
    'JAVA_BINDIR': '/usr/lib/jvm/java/bin',
    'JAVA_HOME': '/usr/lib/jvm/java',
    'JAVA_ROOT': '/usr/lib/jvm/java',
    'JDK_HOME': '/usr/lib/jvm/java',
    'JRE_HOME': '/usr/lib/jvm/jre',
    'LANG': 'POSIX',
    'LC_CTYPE': 'en_US.UTF-8',
    'LESS': '-M -I -R',
    'LESSCLOSE': 'lessclose.sh %s %s',
    'LESSKEY': '/etc/lesskey.bin',
    'LESSOPEN': 'lessopen.sh %s',
    'LESS_ADVANCED_PREPROCESSOR': 'no',
    'LOGNAME': 'root',
    'MACHTYPE': 'i686-suse-linux',
    'MAIL': '/var/mail/root',
    'MANPATH': '/usr/share/man:/usr/local/man',
    'MINICOM': '-c on',
    'MORE': '-sl',
    'NNTPSERVER': 'news',
    'NO_PROXY': 'localhost, 127.0.0.1',
    'OSTYPE': 'linux',
    'PAGER': 'less',
    'PATH': '/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin:/usr/bin/X11:/usr/X11R6/bin:/usr/games',
    'PS1': '[\\\\u@\\\\h: \\\\w]\\\\$ ',
    'PWD': '/root',
    'PYTHONSTARTUP': '/etc/pythonstart',
    'QT_SYSTEM_DIR': '/usr/share/desktop-data',
    'SDK_HOME': '/usr/lib/jvm/java',
    'SDL_AUDIODRIVER': 'pulse',
    'SHELL': '/bin/bash',
    'SHLVL': '1',
    'SSH_CLIENT': '10.83.202.135 54079 22',
    'SSH_CONNECTION': '10.83.202.135 54079 10.83.202.135 22',
    'SSH_SENDS_LOCALE': 'yes',
    'SSH_TTY': '/dev/pts/12',
    'TERM': 'xterm',
    'USER': 'root',
    'WINDOWMANAGER': '/usr/bin/gnome',
    'XCURSOR_THEME': 'DMZ',
    'XDG_CONFIG_DIRS': '/etc/xdg',
    'XDG_DATA_DIRS': '/usr/share',
    'XKEYSYMDB': '/usr/X11R6/lib/X11/XKeysymDB',
    'XNLSPATH': '/usr/share/X11/nls',
    'ftp_proxy': 'http://10.159.224.230:8080',
    'http_proxy': 'http://10.159.224.230:8080',
    'https_proxy': 'http://10.159.224.230:8080',
    'no_proxy': 'localhost, 127.0.0.1'
}

COMMAND_KWARGS = {}

COMMAND_OUTPUT_PS1 = r"""
AP-AWT-LP3-11:~/sstlib/config #export PS1="\h: #"
AP-AWT-LP3-11: #
"""

COMMAND_RESULT_PS1 = {}

COMMAND_KWARGS_PS1 = {
    "ps1_param": r'"\h: #"'
}

COMMAND_OUTPUT_SET = r"""
AP-AWT-LP3-11:~/sstlib/config # export PS1="\e[0;31;1m\h:\w #\e[m"
AP-AWT-LP3-11:~/sstlib/config #
"""

COMMAND_RESULT_SET = {}

COMMAND_KWARGS_SET = {
    "set_param": r'PS1="\e[0;31;1m\h:\w #\e[m"'
}
