# Moler - library to help in building automated tests
**Moler** name is coined by Grzegorz Latuszek with high impact of Bartosz Odziomek, Michał Ernst and Mateusz Smet.

Moler comes from:
![moler_origin](https://github.com/nokia/moler/blob/master/images/moler_origin.png)
* **Mole** :gb:
   * has tunnel-connections to search for data (:bug:) it is processing
   * can detect different bugs hidden under ground
   * **as we want this library to search/detect bugs in tested software**
* **Moler** in spanish :es: means:
   * grind, reduce to powder
   * **as this library should grind tested software to find it's bugs**

-------

## Moler key features:

* Event observers & callbacks (alarms are events example)
  * to allow for online reaction (not offline postprocessing)
* Commands as self-reliant object
  * to allow for command triggering and parsing encapsulated in single object (lower maintenance cost)
* Run observers/commands in the background
  * to allow for test logic decomposition into multiple commands running in parallel
  * to allow for handling unexpected system behavior (reboots, alarms)
* State machines -> automatic auto-connecting after dropped connection
  * to increase framework auto-recovery and help in troubleshooting "what went wrong"
* Automatic logging of all connections towards devices used by tests
  * to decrease investigation time by having logs focused on different parts of system under test

-------

## Library content:

Library provides "bricks" for building automated tests. These bricks:
* have clearly defined responsibilities
* have similar API
* follow same construction pattern (so new ones are easy to create)
