;;
;; This file is part of the sigrok-firmware-fx2lafw project.
;;
;; Copyright (C) 2016 Uwe Hermann <uwe@hermann-uwe.de>
;;
;; This program is free software; you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation; either version 2 of the License, or
;; (at your option) any later version.
;;
;; This program is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.
;;
;; You should have received a copy of the GNU General Public License
;; along with this program; if not, see <http://www.gnu.org/licenses/>.
;;

VID = 0xB504	; Manufacturer ID (0x04B5)
PID = 0x2260	; Product ID (0x6022) = 6022BE
VER = 0x0102	; FW version 0x0201

.include "../descriptor.inc"

; -----------------------------------------------------------------------------
; Strings
; -----------------------------------------------------------------------------

_dev_strings:

; See http://www.usb.org/developers/docs/USB_LANGIDs.pdf for the full list.
string_descriptor_lang 0 0x0409 ; Language code 0x0409 (English, US)

string_descriptor_a 1,^"Hantek"
string_descriptor_a 2,^"DSO-6022BE"
string_descriptor_a 3,^"Custom FW"
_dev_strings_end:
	.dw	0x0000
