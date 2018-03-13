# -*- coding: utf-8 -*-
"""
ps command module.
"""
import logging, re

from moler.cmd.unix.genericunix import GenericUnix


class Ps(GenericUnix):
    def __init__(self,connection=None, cmd='ps'):
        '''Commad Ps is parsed to list of dictionary.
         Each dictionary in list contains all columns defined in columns printed in first line of command result
         Last column may contain more parameters while this field is responsible for process name
         Form of line result:
         {'UID' : 'avahi-a+', 'PID' : 3597, 'PPID' : 1, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : ' 00:00:45',
         'CMD': 'avahi-autoipd: [ens4] sleeping'}
         Each key is derived from first line of executed ps command so accessing it needs ps command with option
         result knowledge '''
        self._cmd_line_found = False
        self._column_line_found = False
        self._columns = list()
        super(Ps, self).__init__(connection)
        self.ret = list()
        logger = logging.getLogger("moler.cmd.unix.ps")
        logger.debug("Command: {}".format(cmd))
        if(self.check_command_correctness(cmd)):
            self.set_unix_command_string(cmd)

    def on_prepare_run(self):
        pass

    def check_command_correctness(self,cmd):
        '''Checking if command passed to Ps class is ps command'''
        if(not re.match(r'\s*ps',cmd)):
            print('\nsetting exception')
            self.set_exception(RuntimeError('Wrong command passed to ps class'))
            return False
        return True

    def on_new_line(self,line):
        '''Operations executed on new line
        columns must be found in order to correct introduce values to dictionary'''
        parsed_line = dict()
        #splitting columns according to column number
        splitted_columns = self.split_columns_in_line(line)
        #when columns are set proceed with putting data to dictionary list
        if (self._columns and splitted_columns != None):
            for  position,column in enumerate(splitted_columns):
                parsed_line[self._columns[position]] = self.convert_data_to_type(splitted_columns[position])
            self.ret.append(parsed_line)
        #assign splitted columns to parameter in Ps class; columns are printed as first line after ps command execution
        if(not self._column_line_found and self._cmd_matched):
            self._columns = splitted_columns
            self._column_line_found = True
        #execute generic on_new_line
        #print(self.ret)
        return super(Ps, self).on_new_line(line)

    def split_columns_in_line(self,line):
        #remove white spaces from start and end of line
        line = re.sub(r'^\s+', '', line)
        line = re.sub(r'\s+$', '', line)
        line = re.split(r'\s+', line)
        # command field may contain white space so it need to be removed
        if(self._columns is not None and line is not None):
            if((len(self._columns) < len(line)) and self._column_line_found):
                base_columns = line[:len(self._columns) - 1]
                elements_to_connect = ' '.join(line[-(len(line) - len(self._columns) + 1 ):])
                base_columns.append(elements_to_connect)
                line = base_columns
            if(len(self._columns) > len(line)):
                line = None
        return line

    def convert_data_to_type(self,data):
        #when casting wrong type Value Error will be raised
        try:
            d_int = int(data)
            if(str(d_int) == data):
                return d_int
        except ValueError:
            pass
        try:
            d_float = float(data)
            return d_float
        except ValueError:
            pass

        return data



   # def get_cmd(self):
    #    print(self.command_string)
     #   return self.command_string

 #   def on_new_line(self,line):
 #           if(self.running()):
 #               self.ret.append(line)
 #           return super(Ps, self).on_new_line(line)
#    def get_final_timeout(self):
#        pass
#
#    def get_pid_to_name(self):
#        pass
#
#    def get_pids(self):
#        pass


COMMAND_OUTPUT_V1 = '''
root@DMICTRL:~# ps -o user,pid,vsz,osz,pmem,rss,cmd -e
 USER       PID    VSZ SZ %MEM   RSS COMMAND
 root         1   1664  -  0.1   572 init [3]  
 root         2      0  -  0.0     0 [ksoftirqd/0]
 root         3      0  -  0.0     0 [desched/0]
 root         4      0  -  0.0     0 [events/0]
 root         5      0  -  0.0     0 [khelper]
 root        10      0  -  0.0     0 [kthread]
 root        34      0  -  0.0     0 [kblockd/0]
 root        67      0  -  0.0     0 [pdflush]
 root        68      0  -  0.0     0 [pdflush]
 root        70      0  -  0.0     0 [aio/0]
 root        69      0  -  0.0     0 [kswapd0]
 root       665      0  -  0.0     0 [kjournald]
 bin        814   1908  -  0.1   544 /sbin/portmap
 root       847   1772  -  0.1   712 /sbin/syslogd -r
 root       855   1664  -  0.0   500 /sbin/klogd -x   
 root@DMICTRL:~# 
 '''

COMMAND_RESULT_V1 = [
{'USER' : 'root', 'PID' : 1, 'VSZ' : 1664, 'SZ' : '-', '%MEM' : 0.1, 'RSS' : 572, 'COMMAND' : 'init [3]'},
{'USER' : 'root', 'PID' : 2, 'VSZ' : 0, 'SZ' : '-', '%MEM' : 0.0, 'RSS' : 0 , 'COMMAND' : '[ksoftirqd/0]'},
{'USER' : 'root', 'PID' : 3, 'VSZ' : 0, 'SZ' : '-', '%MEM' : 0.0, 'RSS' : 0, 'COMMAND' : '[desched/0]'},
{'USER' : 'root', 'PID' : 4, 'VSZ' : 0, 'SZ' : '-', '%MEM' : 0.0, 'RSS' : 0, 'COMMAND' : '[events/0]'},
{'USER' : 'root', 'PID' : 5, 'VSZ' : 0, 'SZ' : '-', '%MEM' : 0.0, 'RSS' : 0, 'COMMAND' : '[khelper]'},
{'USER' : 'root', 'PID' : 10, 'VSZ' : 0, 'SZ' : '-', '%MEM' : 0.0, 'RSS' : 0, 'COMMAND' : '[kthread]'},
{'USER' : 'root', 'PID' : 34, 'VSZ' : 0, 'SZ' : '-', '%MEM' : 0.0, 'RSS' : 0, 'COMMAND' : '[kblockd/0]'},
{'USER' : 'root', 'PID' : 67, 'VSZ' : 0, 'SZ' : '-', '%MEM' : 0.0, 'RSS' : 0, 'COMMAND' : '[pdflush]'},
{'USER' : 'root', 'PID' : 68, 'VSZ' : 0, 'SZ' : '-', '%MEM' : 0.0, 'RSS' : 0, 'COMMAND' : '[pdflush]'},
{'USER' : 'root', 'PID' : 70, 'VSZ' : 0, 'SZ' : '-', '%MEM' : 0.0, 'RSS' : 0, 'COMMAND' : '[aio/0]'},
{'USER' : 'root', 'PID' : 69, 'VSZ' : 0, 'SZ' : '-', '%MEM' : 0.0, 'RSS' : 0, 'COMMAND' : '[kswapd0]'},
{'USER' : 'root', 'PID' : 665, 'VSZ' : 0, 'SZ' : '-', '%MEM' : 0.0, 'RSS' : 0, 'COMMAND' : '[kjournald]'},
{'USER' : 'bin', 'PID' : 814, 'VSZ' : 1908, 'SZ' : '-', '%MEM' : 0.1, 'RSS' : 544, 'COMMAND' : '/sbin/portmap'},
{'USER' : 'root', 'PID' : 847, 'VSZ' : 1772, 'SZ' : '-', '%MEM' : 0.1, 'RSS' : 712, 'COMMAND' : '/sbin/syslogd -r'},
{'USER' : 'root', 'PID' : 855, 'VSZ' : 1664, 'SZ' : '-', '%MEM' : 0.0, 'RSS' : 500, 'COMMAND' : '/sbin/klogd -x'}]

COMMAND_OUTPUT_V2 = '''FZM-FDD-086-ws-kvm:/home/rtg # ps -ef
UID        PID  PPID  C STIME TTY          TIME CMD
avahi-a+  3597     1  0  2017 ?        00:00:45 avahi-autoipd: [ens4] sleeping  
root      3598  3597  0  2017 ?        00:00:00 avahi-autoipd: [ens4] callout dispatcher
root      3681     1  0  2017 ?        00:00:17 /sbin/dhclient6 -6 -cf /var/lib/dhcp6/dhclient6.ens3.conf -lf /var/lib/dhcp6/dhclient6.ens3.lease -pf 
root      3812     1  0  2017 ?        00:00:00 /usr/sbin/xinetd -stayalive -dontfork
root      3814     1  0  2017 ?        00:00:00 /usr/sbin/vsftpd /etc/vsftpd.conf
root      3826     1  0  2017 ?        00:00:02 /usr/sbin/sshd -D
root      3835     2  0  2017 ?        00:00:00 [cifsiod]
root      3867     1  0  2017 ?        00:00:18 /usr/sbin/cron -n
root      3870     1  0  2017 tty1     00:00:00 /sbin/agetty --noclear tty1 linux
avahi-a+  4592     1  0  2017 ?        00:17:15 avahi-autoipd: [ens3] sleeping  
root      4593  4592  0  2017 ?        00:00:00 avahi-autoipd: [ens3] callout dispatcher
root      4648     1  0  2017 ?        00:00:00 /sbin/dhcpcd --netconfig -L -E -HHH -c /etc/sysconfig/network/scripts/dhcpcd-hook -t 0 -h FZM-FDD-086-
root      5823     2  0 Mar09 ?        00:00:03 [kworker/u8:2]
FZM-FDD-086-ws-kvm:/home/rtg #
'''

COMMAND_RESULT_V2 = [
{'UID' : 'avahi-a+', 'PID' : 3597, 'PPID' : 1, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : '00:00:45', 'CMD': 'avahi-autoipd: [ens4] sleeping'},
{'UID' : 'root', 'PID' : 3598, 'PPID' : 3597, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : '00:00:00', 'CMD': 'avahi-autoipd: [ens4] callout dispatcher'},
{'UID' : 'root', 'PID' : 3681, 'PPID' : 1, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : '00:00:17', 'CMD': '/sbin/dhclient6 -6 -cf /var/lib/dhcp6/dhclient6.ens3.conf -lf /var/lib/dhcp6/dhclient6.ens3.lease -pf'},
{'UID' : 'root', 'PID' : 3812, 'PPID' : 1, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : '00:00:00', 'CMD': '/usr/sbin/xinetd -stayalive -dontfork'},
{'UID' : 'root', 'PID' : 3814, 'PPID' : 1, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : '00:00:00', 'CMD': '/usr/sbin/vsftpd /etc/vsftpd.conf'},
{'UID' : 'root', 'PID' : 3826, 'PPID' : 1, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : '00:00:02', 'CMD': '/usr/sbin/sshd -D'},
{'UID' : 'root', 'PID' : 3835, 'PPID' : 2, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : '00:00:00', 'CMD': '[cifsiod]'},
{'UID' : 'root', 'PID' : 3867, 'PPID' : 1, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : '00:00:18', 'CMD': '/usr/sbin/cron -n'},
{'UID' : 'root', 'PID' : 3870, 'PPID' : 1, 'C' : 0, 'STIME' : 2017, 'TTY' : 'tty1', 'TIME' : '00:00:00', 'CMD': '/sbin/agetty --noclear tty1 linux'},
{'UID' : 'avahi-a+', 'PID' : 4592, 'PPID' : 1, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : '00:17:15', 'CMD': 'avahi-autoipd: [ens3] sleeping'},
{'UID' : 'root', 'PID' : 4593, 'PPID' : 4592, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : '00:00:00', 'CMD': 'avahi-autoipd: [ens3] callout dispatcher'},
{'UID' : 'root', 'PID' : 4648, 'PPID' : 1, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : '00:00:00', 'CMD': '/sbin/dhcpcd --netconfig -L -E -HHH -c /etc/sysconfig/network/scripts/dhcpcd-hook -t 0 -h FZM-FDD-086-'},
{'UID' : 'root', 'PID' : 5823, 'PPID' : 2, 'C' : 0, 'STIME' : 'Mar09', 'TTY' : '?', 'TIME' : '00:00:03', 'CMD': '[kworker/u8:2]'},

]