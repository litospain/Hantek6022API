#!/bin/sh

./read_eeprom_256_byte.py
od -Ax -tx1 eeprom_256.dat > eeprom_256.dump
