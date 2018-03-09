Moler - library to help in building automated tests
===================================================

Moler key features

- Event observers & callbacks (alarms are events example)

  - to allow for online reaction (not offline postprocessing)

- Commands as self-reliant object

  - to allow for command triggering and parsing encapsulated in single object (lower maintenance cost)

- Run observers/commands in the background

  - to allow for test logic decomposition into multiple commands running in parallel
  - to allow for handling unexpected system behavior (reboots, alarms)

- State machines -> automatic auto-connecting after dropped connection

  - to increase framework auto-recovery and help in troubleshooting "what went wrong"

- Automatic logging of all connections towards devices used by tests

  - to decrease investigation time by having logs focused on different parts of system under test


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   modules
   examples


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
