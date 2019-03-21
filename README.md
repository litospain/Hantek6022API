# Hantek6022API

[![Build status](https://ci.appveyor.com/api/projects/status/github/Ho-Ro/Hantek6022API?branch=master&svg=true)](https://ci.appveyor.com/project/Ho-Ro/Hantek6022API/branch/master) [![Stability: Experimental](https://masterminds.github.io/stability/experimental.svg)](https://masterminds.github.io/stability/experimental.html)

This repo is based on the excellent work of [Robert](https://github.com/rpcope1/Hantek6022API) 
and [Jochen](https://github.com/jhoenicke/Hantek6022API) 
and focusses mainly on Hantek6022BE under Linux (development system: debian buster).

__Hantek6022BE custom firmware is now feature complete and usable for https://github.com/Ho-Ro/openhantek__

__Hantek6022BL custom firmware is not tested - USE WITH CARE!__

<img alt="Scope Visualisation Example" width="100%" src="docs/images/HT6022BEBuiltInOscillator.png">

Hantek 6022BE Python API for Windows and Linux. This is a API for Python via ctypes for Hantek's SDK for the 
ultra-cheap,  reasonably usable (and hackable) 6022BE DSO, with a libusb implementation via libusb1 for Linux. 
I was tired of using the silly Chinese software that came with this DSO, so I decided to write an API so I could run
the scope through Python. 

The scope can be accessed by instantiating an oscilloscope object with the correct scopeid (always 0 for one scope
attached). Things like voltage divisions and sampling rates can be set by the appropriate methods. As I finish developing
this, I will include documentation. Each method has some documentation as to what it does currently though, and hopefully
variable names are clear enough to give you some idea what they are for. 

(Also, the provided DLLs that access the scope belong to Hantek, not me. They are provided simply for ease of access and
are probably NOT covered by the GPL!)

## Neat things you can do

While this scope isn't quite as poweful as your many-thousand dollar Tektronix or even your run of the mill Rigol 1102E,
with a little bit of programming, it's capable of doing interesting things. User -johoe on reddit was able to use
[this library and scope to launch a successful side-channel attack on his TREZOR bitcoin device, and extract the
device's private keys](http://www.reddit.com/r/TREZOR/comments/31z7hc/extracting_the_private_key_from_a_trezor_with_a/#);
yes side-channel attacks aren't just for NSA spooks and crusty academics anymore, even you can do it in your home
with this inexpensive USB scope. :)

If you have you have your own examples or have seen this library used, please let me know so I can add the examples here.

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
 4. Test 6022BL firmware (difficult due to missing hw info and missing device).

One excellent ultimate goal for this would to make it play nice with cheap ARM SBCs like the Raspberry Pi, such that
this could be used as a quick and dirty DAQ for many interesting systems.


For additional (interesting) details, the inquisitive reader should take two or three hours and read:
http://www.eevblog.com/forum/testgear/hantek-6022be-20mhz-usb-dso/ 

UPDATE: If you're interested in contributing and updating this repo, I'd be glad to have help maintaining it.
 I do accept pull requests.
