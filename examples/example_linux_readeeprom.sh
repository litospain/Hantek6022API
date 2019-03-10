#!/bin/sh

./example_linux_readeeprom.py
od -Ax -tx1 eeprom.dat > eeprom.dump
