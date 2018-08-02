[![Build Status](https://travis-ci.org/nokia/moler.svg?branch=master)](https://travis-ci.org/nokia/moler)
[![Coverage Status](https://coveralls.io/repos/github/nokia/moler/badge.svg?branch=master)](https://coveralls.io/github/nokia/moler?branch=master)
[![BCH compliance](https://bettercodehub.com/edge/badge/nokia/moler?branch=master)](https://bettercodehub.com/)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/355afc9110f34d549b7c08c33961827c)](https://www.codacy.com/app/mplichta/moler?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=nokia/moler&amp;utm_campaign=Badge_Grade)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](./LICENSE)

# Table of Contents
1. [Moler](#moler)
   * [Moler key features](#moler-key-features)
   * [Library content](#library-content)
2. [API design reasoning](#api-design-reasoning)
   * [Command as future](#command-as-future)
   * [Command vs. Connection-observer](#command-vs-connection-observer)
   * [Most well known Python's futures are](#most-well-known-pythons-futures)
   * [Fundamental difference of command](#fundamental-difference-of-command)
3. [Designed API](#designed-api)

# Moler
Moler is library to help in building automated tests. Name is coined by Grzegorz Latuszek with high impact of Bartosz Odziomek, Michał Ernst and Mateusz Smet.

Moler comes from:
![moler_origin](https://github.com/nokia/moler/blob/master/images/moler_origin.png)
* **Mole** :gb:
   * has tunnel-connections to search for data (:bug:) it is processing
   * can detect different bugs hidden under ground
   * **as we want this library to search/detect bugs in tested software**
* **Moler** in spanish :es: means:
   * grind, reduce to powder
   * **as this library should grind tested software to find it's bugs**

## Moler key features
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

## Library content
Library provides "bricks" for building automated tests:
* have clearly defined responsibilities
* have similar API
* follow same construction pattern (so new ones are easy to create)

# API design reasoning
The main goal of command is its usage simplicity: just run it and give me back its result.

Command hides from its caller:
* a way how it realizes "runs"
* how it gets data of output to be parsed
* how it parses that data

Command shows to its caller:
* API to start/stop it or await for its completion
* API to query for its result or result readiness

Command works as [Futures and promises](https://en.wikipedia.org/wiki/Futures_and_promises)

After starting, we await for its result which is parsed out command output provided usually as dict.
Running that command and parsing its output may take some time, so till that point result computation is yet incomplete.

## Command as future
* it starts some command on device/shell over connection
  (as future-function starts it's execution)
* it parses data incoming over such connection
  (as future-function does it's processing)
* it stores result of that parsing
  (as future-function concludes in calculation result)
* it provides means to return that result
  (as future-function does via 'return' or 'yield' statement)
* it's result is not ready "just-after" calling command
  (as it is with future in contrast to function)

So command should have future API.

Quote from **_"Professional Python"_** by **Luke Sneeringer**:
> The Future is a standalone object. It is independent of the actual function that is running.
> It does nothing but store the state and result information.

Command differs in that it is both:
* function-like object performing computation
* future-like object storing result of that computation.

## Command vs. Connection-observer
Command is just "active version" of connection observer.

Connection observer is passive since it just observes connection for some data;
data that may just asynchronously appear (alarms, reboots or anything you want).
Intention here is split of responsibility: one observer is looking for alarms,
another one for reboots.

Command is active since it actively triggers some output on connection
by sending command-string over that connection. So, it activates some action
on device-behind-connection. That action is "command" in device terminology.
Like `ping` on bash console/device. And it produces that "command" output.
That output is what Moler's Command as connection-observer is looking for.

## Most well known Python's futures
* [concurrent.futures.Future](https://docs.python.org/3/library/concurrent.futures.html)
* [asyncio.Future](https://docs.python.org/3/library/asyncio-task.html#future)

| API                     | concurrent.futures.Future                   | asyncio.Future                                      |
| :---------------------- | :------------------------------------------ | :-------------------------------------------------- |
| storing result          | :white_check_mark: `set_result()`           | :white_check_mark: `set_result()`                   |
| result retrieval        | :white_check_mark: `result()`               | :white_check_mark: `result()`                       |
| storing failure cause   | :white_check_mark: `set_exception()`        | :white_check_mark: `set_exception()`                |
| failure cause retrieval | :white_check_mark: `exception()`            | :white_check_mark: `exception()`                    |
| stopping                | :white_check_mark: `cancel()`               | :white_check_mark: `cancel()`                       |
| check if stopped        | :white_check_mark: `cancelled()`            | :white_check_mark: `cancelled()`                    |
| check if running        | :white_check_mark: `running()`              | :no_entry_sign: `(but AbstractEventLoop.running())` |
| check if completed      | :white_check_mark: `done()`                 | :white_check_mark: `done()`                         |
| subscribe completion    | :white_check_mark: `add_done_callback()`    | :white_check_mark: `add_done_callback()`            |
| unsubscribe completion  | :no_entry_sign:                             | :white_check_mark: `remove_done_callback()`         |

Starting callable to be run "as future" is done by entities external to future-object

| API              | concurrent.futures<br>start via Executor objects (thread/proc) | asyncio<br>start via module-lvl functions or ev-loop |
| ---------------- | ---------------------------------------- | ---------------------------------------------- |
| start callable   | submit(fn, *args, **kwargs)<br>Schedules callable to be executed as<br>fn(*args **kwargs) -> Future | ensure_future(coro_or_future) -> Task<br>future = run_coroutine_threadsafe(coro, loop) |
| start same callable<br>on data iterator | map(fn, *iterables, timeout) -> iterator | join_future = asyncio.gather(*map(f, iterable))<br>loop.run_until_complete(join_future)|

Awaiting completion of future is done by entities external to future-object

| API               | concurrent.futures<br>awaiting by module level functions | asyncio<br>awaiting by module-lvl functions or ev-loop |
| ----------------- | ------------------------------------------ | -------------------------------------------- |
| await completion  |  done, not_done = wait(futures, timeout) -> futures | done, not_done = await wait(futures)<br>results = await gather(futures)<br>result = await future<br>result = yield from future<br>result = await coroutine<br>result = yield from coroutine<br>result = yield from wait_for(future, timeout)<br>loop.run_until_complete(future) -> blocking run |
| process as they<br>complete | for done in as_completed(futures, timeout) -> futures | for done in as_completed(futures, timeout) -> futures |

## Fundamental difference of command
Contrary to **concurrent.futures** and **asyncio** we don't want command to be run by some external entity.
We want it to be self-executable for usage simplicity.
We want to take command and just say to it:
* **"run"** or **"run in background"**
* and not **"Hi, external runner, would you run/run-background that command for me"**

# Designed API
1. create command object
``` python
command = Command()
```

2. run it synchronously/blocking and get result in one shot behaves like function call since Command is callable.

Run-as-callable gives big advantage since it fits well in python ecosystem.
``` python
result = command()
```
function example:
``` python
map(ping_cmd, all_machines_to_validate_reachability)
```

3. run it asynchronously/nonblocking
``` python
command_as_future = command.start()
```

4. shift from background to foreground

**asyncio:** variant looks like:
``` python
result = await future
done_futures, pending = yield from asyncio.wait(futures)
result = yield from asyncio.wait_for(future, 60.0)
```
and **concurrent.futures** variant looks like:
``` python
done_futures, pending = wait(futures)
```
Moler's API maps to above well-known API
``` python
result = command.await_done(timeout)
```
* it is "internal" to command "Hi command, that is what I want from you" (above APIs say "Hi you there, that is what I want you to do with command")
* it directly (Zen of Python) shows what we are awaiting for
* timeout is required parameter (not as in concurrent.futures) since we don't expect endless execution of command (user must know what is worst case timeout to await command completion)
