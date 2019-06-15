# Hantek6022API

[![Build status](https://ci.appveyor.com/api/projects/status/github/Ho-Ro/Hantek6022API?branch=master&svg=true)](https://ci.appveyor.com/project/Ho-Ro/Hantek6022API/branch/master)
[![CodeFactor](https://www.codefactor.io/repository/github/ho-ro/hantek6022api/badge)](https://www.codefactor.io/repository/github/ho-ro/hantek6022api)
[![Stability: Active](https://masterminds.github.io/stability/active.svg)](https://masterminds.github.io/stability/active.html)

This repo is based on the excellent work of [Robert](https://github.com/rpcope1/Hantek6022API) 
and [Jochen](https://github.com/jhoenicke/Hantek6022API) 
and focusses mainly on Hantek6022BE/BL under Linux (development system: debian buster).

__Hantek6022BE custom firmware is feature complete and usable for [OpenHantek6022](https://github.com/OpenHantek/OpenHantek6022)__

__Hantek6022BL custom firmware is feature complete but not as intensively tested as the BE version__

<img alt="Scope Visualisation Example" width="100%" src="docs/images/HT6022BEBuiltInOscillator.png">


Hantek 6022 Python API for Linux. This is a API for Python for the
ultra-cheap, reasonably usable (and hackable) 6022 DSO, with a libusb implementation via libusb1 for Linux.

The scope can be accessed by instantiating an oscilloscope object with the correct scopeid (always 0 for one scope
attached). Things like voltage divisions and sampling rates can be set by the appropriate methods. As I finish developing
this, I will include documentation. Each method has some documentation as to what it does currently though, and hopefully
variable names are clear enough to give you some idea what they are for.

## Neat things you can do

While this scope isn't quite as poweful as your many-thousand dollar Tektronix or even your run of the mill Rigol 1102E,
with a little bit of programming, it's capable of doing interesting things. User -johoe on reddit was able to use
[this library and scope to launch a successful side-channel attack on his TREZOR bitcoin device, and extract the
device's private keys](http://www.reddit.com/r/TREZOR/comments/31z7hc/extracting_the_private_key_from_a_trezor_with_a/#);
yes side-channel attacks aren't just for NSA spooks and crusty academics anymore, even you can do it in your home
with this inexpensive USB scope. :)

If you have you have your own examples or have seen this library used, please let me know so I can add the examples here.

## Create calibration values for OpenHantek

As you can see in the trace above the scope has a quite big zero point error (the measured real signal switches between 0.0 V and 2.0 V) - also the gain is defined by resistors with 5% tolerance in the frontend - in best case by two resistors R27/17 & R31/21 in the chain (x1), in worst case by four resistors R27/17 & R31/21 & R32/23 & R18/19/22 in the chain (x2, x5, x10). 

-> https://github.com/Ho-Ro/Hantek6022API/blob/master/hardware/6022BE_Frontend_with_pinout.jpg 

In the end you can have a statistical gain tolerance of about 7%...10% -> RSS analysis (root sum square, square all tolerances, sum them up und calculate the root of this sum) gives an expected tolerance range:

- sqrt( 2 * (5%)² ) = 1.4 * 5% = 7% for gain step x1
- sqrt( 4 * (5%)² ) = 2 * 5% = 10% for all other gains

To reduce this effect OpenHantek uses individual correction values:
1. Offset and gain calibration are read from a calibration file `~/.config/OpenHantek/modelDSO6022.conf`
2. If this file is not available offset and calibration will be read from eeprom.

Step 2 uses the factory offset calibration values in eeprom.
Out of the box only offset values are contained in eeprom,
the simple program `cal_zero.py` allows to update these values in case the offset has changed over time.
Apply 0 V to both inputs (e.g. connect both probes to the GND calibration connector) and execute:

    python examples/examples_libusb/cal_zero.py

The more complex program `calibrate.py` measures and stores also gain calibration.
To calibrate gain you have to apply a well known voltage (setpoint)
and compare it with the actual value that is read by the scope:

    python examples/examples_libusb/calibrate.py

This program guides you through the process.
You have to apply several different voltages to both input,
the program measures and compares them against the expected gain settings:

1. Apply 0 V. The Program reads the raw channel values and calculates all offset values
2. Apply 0.4 V. The program measures the gain for range x10
3. Apply 0.8 V. The program measures the gain for range x5
4. Apply 2.0 V. The program measures the gain for range x2
5. Apply 4.0 V. The program measures the gain for range x1
6. The program stores the calibration values in eeprom
7. The program creates a config file `modelDSO6022.conf`

This config file can be copied into directory `~/.config/OpenHantek`.
On every startup OpenHantek reads this file and applies the calibratipon accordingly.

The calibration voltages do not have to correspond absolutely to the given value,
but the applied voltage should not be much higher than the given value and must be determined exactly -
e.g. by measuring it with a multimeter. Type in the measured voltage at the prompt.
4 AA batteries in a battery holder are a simple and reliable voltage source:

Requested Voltage | Applied Voltage | Comment
------------------|-----------------|--------
0.4 V             | 0.3 V           | 2 x AA with 1/10 probe
0.8 V             | 0.6 V           | 4 x AA with 1/10 probe
2.0 V             | 1.5 V           | 1 x AA
4.0 V             | 3.0 V or 4.5 V  | 2 or 3 x AA

[Read more about the eeprom content...](docs/README.md#eeprom)

## Now with Linux support

If you're on Linux, you're also in luck. Provided are some reverse engineered binding for libusb to operate this 
little device. You may wish to first add 60-hantek-6022-usb.rules to your udev rules, via

    sudo cp 60-hantek-6022-usb.rules /etc/udev/rules.d/

After you've done this, the scope should automatically come up with the correct permissions to be accessed without a
root user.

The following instructions are tested with Debian (Stretch and Buster) and are executed also automatically under Ubuntu (1804) - have a look at the [appveyor build status](https://ci.appveyor.com/project/Ho-Ro/Hantek6022API/branch/master) and the [related config file](https://github.com/Ho-Ro/Hantek6022API/blob/master/appveyor.yml).

To compile the custom firmware you have to install (as root) the _small devices c compiler_ sdcc:

    sudo apt install sdcc

The firmware uses the submodule [fx2lib](https://github.com/djmuhlestein/fx2lib/tree/4d3336c3b5ebc2127a8e3c013ea13ad58873e9e0), pull it in:

    git submodule update --init

To build the custom firmware run `make` in the top level directory:

    make

To build and install the python package you have to install some more .deb packages:

    sudo apt install python3-setuptools python3-libusb1

Build and install the python modules and the firmware (e.g. into /usr/local/lib/python3.5/dist-packages/Python-Hantek...).

    sudo python3 setup.py install

Or use the Makefile:

    sudo make install

To build a debian package you need two more packages:

    (sudo) apt install checkinstall fakeroot

Create a debian package:

    make deb

that can be installed with

    sudo dpkg -i dist/hantek6022api_...

With the device plugged in, run the flashfirmware.py example,

    python examples/examples_libusb/flash_firmware_custom.py

to bootstrap the scope for use. You can then write your own programs, or look at the current channel 1 scope trace via

    python examples/examples_libusb/scopevis.py

## TODO

 1. Clean up library, apply good formatting.
 2. Clean up unit tests.
 3. Add more examples.

One excellent ultimate goal for this would to make it play nice with cheap ARM SBCs like the Raspberry Pi, such that
this could be used as a quick and dirty DAQ for many interesting systems.

For additional (interesting) details, the inquisitive reader should take two or three hours and read:
http://www.eevblog.com/forum/testgear/hantek-6022be-20mhz-usb-dso/ 

UPDATE: If you're interested in contributing and updating this repo, I'd be glad to have help maintaining it.
 I do accept pull requests.
