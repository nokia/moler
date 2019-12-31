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
