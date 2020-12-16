// .. Copyright (C) 2012-2020 Bryan A. Jones.
//
//  This file is part of the CellBotics system.
//
//  The CellBotics system is free software: you can redistribute it and/or
//  modify it under the terms of the GNU General Public License as
//  published by the Free Software Foundation, either version 3 of the
//  License, or (at your option) any later version.
//
//  The CellBotics system is distributed in the hope that it will be
//  useful, but WITHOUT ANY WARRANTY; without even the implied warranty
//  of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//  General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with the CellBotics system.  If not, see
//  <http://www.gnu.org/licenses/>.
//
// ***********************************************************************
// |docname| - JavaScript code to integrate the CellBot module into Skulpt
// ***********************************************************************
// This is based on the instruction under the "Adding a Module" heading of `Programming Skulpt <https://skulpt.org/docs/index.html>`_.
var $builtinmodule = function(name)
{
    var mod = {};
    let ble = cell_bot_ble_gui && cell_bot_ble_gui.cell_bot_ble;

    // This function turns a JavaScript Promise into its Skulpt equivalent, a suspension.
    function promiseToSkulpt(promise_) {
        let susp = new Sk.misceval.Suspension();
        let resolution;

        susp.resume = function() {
            return resolution;
        };

        susp.data = {
            type: "Sk.promise",
            promise: promise_.then(function(value) {
                resolution = Sk.ffi.remapToPy(value);
                return value;
            }, function(err) {
                resolution = "";
                return err;
            })
        };

        return susp;
    }

    mod.CellBot = Sk.misceval.buildClass(mod, function($gbl, $loc) {
        $loc.__init__ = new Sk.builtin.func(function(self) {
            if (ble === undefined || !ble.paired()) {
                throw "The CellBot is not paired. Click on the Pair button before running your program.";
            }
        });

        // We can only define these if we can get to ``ble``.
        if (ble) {
            $loc.INPUT = new Sk.builtin.int_(ble.INPUT);
            $loc.OUTPUT = new Sk.builtin.int_(ble.OUTPUT);
        }

        $loc.pinMode = new Sk.builtin.func(function(self, pin, mode) {
            return promiseToSkulpt(ble.pinMode(Sk.ffi.remapToJs(pin), Sk.ffi.remapToJs(mode)));
        });

        $loc.digitalWrite = new Sk.builtin.func(function(self, pin, value) {
            return promiseToSkulpt(ble.digitalWrite(Sk.ffi.remapToJs(pin), Sk.ffi.remapToJs(value)));
        });

        $loc.digitalRead = new Sk.builtin.func(function(self, pin) {
            return promiseToSkulpt(ble.digitalRead(Sk.ffi.remapToJs(pin)));
        });

        $loc.ledcSetup = new Sk.builtin.func(function(self, u8_channel, d_freq, u8_resolution_bits) {
            return promiseToSkulpt(ble.ledcSetup(Sk.ffi.remapToJs(u8_channel), Sk.ffi.remapToJs(d_freq), Sk.ffi.remapToJs(u8_resolution_bits)));
        });

        $loc.ledcAttachPin = new Sk.builtin.func(function(self, u8_pin, u8_channel) {
            return promiseToSkulpt(ble.ledcAttachPin(Sk.ffi.remapToJs(u8_pin), Sk.ffi.remapToJs(u8_channel)));
        });

        $loc.ledcWrite = new Sk.builtin.func(function(self, u8_channel, u32_duty) {
            return promiseToSkulpt(ble.ledcWrite(Sk.ffi.remapToJs(u8_channel), Sk.ffi.remapToJs(u32_duty)));
        });

    }, 'CellBot', []);

    return mod;
}
/* Test code
import cellbotics

# Define the pin numbers we need.
LED1 = 2
PB1 = 0

# Set up PWM
channel = 0

# Setup
cb = cellbotics.CellBot()
cb.pinMode(LED1, cb.OUTPUT)
cb.pinMode(PB1, cb.INPUT)
cb.ledcSetup(channel, 1000, 16)
cb.ledcAttachPin(LED1, channel)

val, msg = cb.digitalRead(PB1)
print(f"The pushbutton is {val}.")
cb.ledcWrite(channel, 5000 + 25000*val)
#debugger;
*/