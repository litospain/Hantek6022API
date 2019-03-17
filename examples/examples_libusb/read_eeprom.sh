#!/bin/sh

./read_eeprom.py
od -Ax -tx1 eeprom.dat > eeprom.dump
