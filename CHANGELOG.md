## moler 1.10.0

### Improved
* Classes Connection and ObservableConnection are deprecated now. Their original code has been moved into
 AbstractMolerConnection and ThreadedMolerConnection. Change made for code clarity.

### Fixed
* Iperf2 command fails on parsing when used `with -s -P 1` options (single run server)

## moler 1.9.0

### Added
* New method of converting string to int for whole dict.

### Improved
* Keep state in background does not block main flow
* data_received() of commands & events gets additional parameter: time when data was caught on connection
* Improvement parsing in command ls.
* Commands, events and callbacks data processing is done in separate thread to secure connection reads against blocking
 them by commands/events/callbacks.

## moler 1.8.0

### Added
* AdbRemote device - new state ADB_SHELL_ROOT
   * allow firing android-linux commands that need root
* access to .start_time of any ConnectionObserver
   * help in extending its timeout (calculating its "already passed life-time")

### Improved
* hardening Iperf2 against multiple echo at command startup (observed under cygwin)
* better display of regexp patterns in logs - simplify troubleshooting
* str(CommandChangingPrompt) display expected prompt regexp - simplify troubleshooting
* cmd.unix.exit.Exit got new parameter allowed_newline_after_prompt
   * allowed_newline_after_prompt=True helps to operate with cygwin

## moler 1.7.0

### Added
* AdbRemote device being state machine capable to reach ADB_SHELL state
   * allow firing android-linux commands from within android device
* ADB commands:
   * adb_shell
* AT commands:
   * plink_serial

### Improved
* AtRemote device uses 'plink -serial' to proxy serial into stdin/stdout
* State Machines definition: commands allowed for state may be specified using module name
   * previously (only packages): ['moler.cmd.at'], now: ['moler.cmd.at', 'moler.cmd.unix.ctrl_c']
   * helps in code reuse while keeping commands under related device folder
* Improved connection decoder inside ThreadedTerminal: cleaning output from VT100 terminal codes (not all)

### Fixed
* GenericAtCommand treats 'NO CARRIER' console output as error indication

## moler 1.6.0

### Added
* Publisher class - Moler implementation of Publisher-Subscriber Design Pattern
* Iperf2 command publishing intermediate reports to all subscribed "observers"
* AT commands:
   * at(AT)
   * attach(AT+CGATT=1), detach(AT+CGATT=0), get_attach_state(AT+CGATT?)
   * get_imei(AT+CGSN)
   * get_imsi(AT+CIMI)
   * get_manufacturer_id(AT+CGMI)
   * get_revision_id(AT+CGMR)
* moler_serial_proxy tool proxing between serial connection and stdio/stdout
* AtRemote device being state machine capable to reach AT_REMOTE state and issue AT commands
   * (controlling AT console available over serial connection on remote machine)

### Improved
* CommandTextualGeneric may set direct path to command executable
   * (f.ex. OS may default 'iperf' to '/usr/bin/iperf' but user wants '/usr/local/bin/iperf')

### Fixed
* ConnectionObserver, AbstractDevice were unable to be used inside multiple inheritance

## moler 1.5.1

### Fixed
* SSH regex for fingerptint prompt

## moler 1.5.0

### Added
* Termianl binary debug

### Improved
* CI pipeline
* ls command

### Changed
* Redefined timeout for telnet and ssh
* RegexHelper checks if parameter is not None


## moler 1.4.0

### Changed
* connection name returned by iperf2 uses "port@host" format to not confuse on IPv6 (fd00::1:0:5901 -> 5901@fd00::1:0)

### Deprecated
* `config_type` parameter of `load_config()` is not needed, configuration type is autodetected


## moler 1.3.1

### Added
* possibility to enable/disable logging each occurrence of event
* backward compatibility for load_device_from_config()

### Fixed
* device closing (dev.remove() method) fails if device was already closed


## moler 1.3.0

### Added
* force Unix device to return into local shell when device is closing (that would close ssh if was open)
* allow adding devices after initial load of configuration
* new UNIX command handled by moler: **devmem**
* iperf command refactored into iperf2 command

### Fixed
* wrong iperf bandwidth calculation when bandwidth displayed in Kbits/sec, Mbits/sec, Gbits/sec
* first moler prompt to catch
* removal of new line characters on some connections

### Deprecated
* stop using Iperf command from moler.cmd.unix.iperf; use Iperf2 from moler.cmd.unix.iperf2 instead


## moler v1.2.0

### Added
* Possibility to forget device
* Change number of retry whe terminal not operable yet

### Fixed
* fix calculating timeout of sudo command


## moler v1.1.0

### Added
* new UNIX command handled by moler: **gzip**
* skip asyncio test under python 2 (internal CI of moler)

### Fixed
* wrong processing of chunked lines by textual events
* sudo command incorrectly handling result of sudo-embedded command


## moler v1.0.1

### Added
* improved documentation generation


## moler v1.0.0

### Added
* first official release of Moler
