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
    function promiseToPy(promise_) {
        let susp = new Sk.misceval.Suspension();
        let resolution;
        let exception;

        susp.resume = function() {
            if (exception) {
                throw exception;
            } else {
                return resolution;
            }
        }

        susp.data = {
            type: "Sk.promise",
            promise: promise_.then(function(value) {
                resolution = Sk.ffi.remapToPy(value);
                return value;
            }, function(err) {
                exception = err;
                return err;
            })
        };

        return susp;
    }

    // Returns a function that calls the provided JavaScript function on the provided Python parameters, first converting the parameters to JavaScript.
    function remapToJsFunc(
        // The JavaScript function to invoke.
        js_func,
        // The expected number of arguments for this function; if this is empty, no argument checking is performed. Otherwise, this is passed directly to ``Sk.builtin.pyCheckArgs`` (defined in ``src/function.js``):
        ...expected_args
        //
        // Note: it would be nice to simply query ``js_func`` for the number of arguments, but this is `hard <https://stackoverflow.com/questions/1007981/how-to-get-function-parameter-names-values-dynamically>`_.
    ) {
        return function(
            // The arguments from Python.
            ...args
        ) {
            if (expected_args) {
                // Convert a number to an array, so we can use it in the spread below.
                Sk.builtin.pyCheckArgs(js_func.toString(), args, ...expected_args);
            }

            // We don't care about converting the Python class to JS, and in fact don't need it. Strip it out. In the future, consider storing the JS class in the value returned to Python and using that.
            args = args.slice(1);

            // Convert all args to JS. Convert the return type back to Python (handling a Promise if necessary).
            let ret = js_func(...args.map(x => Sk.ffi.remapToJs(x)));
            return (ret instanceof Promise) ? promiseToPy(ret) : ret;
        }
    }

    mod.CellBot = Sk.misceval.buildClass(mod, function($gbl, $loc) {
        $loc.__init__ = new Sk.builtin.func(function(self) {
            if (ble === undefined || !ble.paired()) {
                throw "The CellBot is not paired. Click on the Pair button before running your program.";
            }
        });

        $loc.INPUT = new Sk.builtin.int_(CellBotBle.INPUT);
        $loc.OUTPUT = new Sk.builtin.int_(CellBotBle.OUTPUT);

        $loc.resetHardware = new Sk.builtin.func(remapToJsFunc(ble.resetHardware, 0));
        $loc.pinMode = new Sk.builtin.func(remapToJsFunc(ble.pinMode, 2));
        $loc.digitalWrite = new Sk.builtin.func(remapToJsFunc(ble.digitalWrite, 2));
        $loc.digitalRead = new Sk.builtin.func(remapToJsFunc(ble.digitalRead, 1));
        $loc.ledcSetup = new Sk.builtin.func(remapToJsFunc(ble.ledcSetup, 3));
        $loc.ledcAttachPin = new Sk.builtin.func(remapToJsFunc(ble.ledcAttachPin, 2));
        $loc.ledcDetachPin = new Sk.builtin.func(remapToJsFunc(ble.ledcAttachPin, 1));
        $loc.ledcWrite = new Sk.builtin.func(remapToJsFunc(ble.ledcWrite, 2));

    }, 'CellBot', []);

    return mod;
}
