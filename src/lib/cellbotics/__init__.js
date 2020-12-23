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
//
// Utilities
// =========
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
    // The expected number of arguments for this function; if empty, no argument checking is performed. Otherwise, this parameter is passed directly to ``Sk.builtin.pyCheckArgs`` (defined in ``src/function.js``):
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
            Sk.builtin.pyCheckArgs(js_func.name, args, ...expected_args);
        }

        // Drop the first argument (self) when calling the JavaScript equivalent -- the function to call is already a method of a class, so ``self`` isn't needed.
        args = args.slice(1);

        // Convert all args to JS. Convert the return type back to Python (handling a Promise if necessary).
        let ret = js_func(...args.map(x => Sk.ffi.remapToJs(x)));
        return (ret instanceof Promise) ? promiseToPy(ret) : ret;
    }
}


let get_self = self => self && self.__js_class;

// A handy shortcut for wrapping methods in this class.
let method_wrap = (method_name, num_args) => new Sk.builtin.func(
    (...args) =>
        remapToJsFunc(get_self(args[0])[method_name], num_args, num_args)(...args)
);

let prop_wrap = prop_name => new Sk.builtin.func(
    (...args) => {
        Sk.builtin.pyCheckArgs(prop_name, args, 1, 1);
        return Sk.ffi.remapToPy(get_self(args[0])[prop_name]);
    }
);


// Python cellbotics module
// ========================
// This is based on the instruction under the "Adding a Module" heading of `Programming Skulpt <https://skulpt.org/docs/index.html>`_.
var $builtinmodule = function(name)
{
    var mod = {};

    mod.CellBot = Sk.misceval.buildClass(mod, function($gbl, $loc) {
        let ble = cell_bot_ble_gui && cell_bot_ble_gui.cell_bot_ble;

        $loc.__init__ = new Sk.builtin.func(function(self) {
            if (!ble.paired()) {
                throw "The CellBot is not paired. Click on the Pair button before running your program.";
            }

            // Reset the hardware before doing any other hardware operation. Since the constructor must return null, call it this way:
            return promiseToPy(ble.resetHardware().then(() => undefined));
        });

        // Define Arduino constants.
        $loc.INPUT = new Sk.builtin.int_(ble.INPUT);
        $loc.OUTPUT = new Sk.builtin.int_(ble.OUTPUT);

        // The way we wrap all these JavaScript methods to embed them in Skulpt.
        let wrap = (f, num_args) =>
            new Sk.builtin.func(remapToJsFunc(f, num_args, num_args));

        // Provide Arduino functions via a JavaScript RPC.
        $loc.resetHardware = wrap(ble.resetHardware, 1);
        $loc.pinMode = wrap(ble.pinMode, 3);
        $loc.digitalWrite = wrap(ble.digitalWrite, 3);
        $loc.digitalRead = wrap(ble.digitalRead, 2);
        $loc.ledcSetup = wrap(ble.ledcSetup, 4);
        $loc.ledcAttachPin = wrap(ble.ledcAttachPin, 3);
        $loc.ledcDetachPin = wrap(ble.ledcDetachPin, 2);
        $loc.ledcWrite = wrap(ble.ledcWrite, 3);

    }, 'CellBot', []);


    // Create an "Abstract" base class that has non-functional start and stop methods.
    mod._Sensor = Sk.misceval.buildClass(mod, function($gbl, $loc) {
        $loc.start = method_wrap("start", 1);
        $loc.stop = method_wrap("stop", 1);

    }, "_Sensor", []);


    // Subclass this to produce another "abstract" base class for xyz readings.
    mod._XYZSensor = Sk.misceval.buildClass(mod, function($gbl, $loc) {
        $loc.x = prop_wrap("x", 1);
        $loc.y = prop_wrap("y", 1);
        $loc.z = prop_wrap("z", 1);

    }, "_XYZSensor", [mod._Sensor]);


    // Repeat for orientation sensors.
    mod._OrientationSensor = Sk.misceval.buildClass(mod, function($gbl, $loc) {
        $loc.quaternion = prop_wrap("quaternion", 1);

    }, "_OrientationSensor", [mod._Sensor]);


    // Create a factory for making classes for these sensors.
    let sensor_factory = (py_name, py_superclass, js_class) =>
        mod[py_name] = Sk.misceval.buildClass(mod, function($gbl, $loc) {
            $loc.__init__ = new Sk.builtin.func(function(...args) {
                Sk.builtin.pyCheckArgs("__init__", [args], 1, 1);
                args[0].__js_class = new js_class();
            });

        }, py_name, [py_superclass]);

    // Concrete classes
    ///================
    mod.AmbientLightSensor = Sk.misceval.buildClass(mod, function($gbl, $loc) {
        $loc.__init__ = new Sk.builtin.func(function(...args) {
            Sk.builtin.pyCheckArgs("__init__", [args], 1, 1);
            args[0].__js_class = new SimpleAmbientLightSensor();
        });

        $loc.illuminance = prop_wrap("illuminance");

    }, "AmbientLightSensor", [mod._Sensor]);

    mod.GeolocationSensor = Sk.misceval.buildClass(mod, function($gbl, $loc) {
        $loc.__init__ = new Sk.builtin.func(function(...args) {
            Sk.builtin.pyCheckArgs("__init__", [args], 1, 1);
            args[0].__js_class = new SimpleGeolocationSensor();
        });

        $loc.latitude = prop_wrap("latitude");
        $loc.longitude = prop_wrap("longitude");
        $loc.altitude = prop_wrap("altitude");
        $loc.accuracy = prop_wrap("accuracy");
        $loc.altitudeAccuracy = prop_wrap("altitudeAccuracy");
        $loc.heading = prop_wrap("heading");
        $loc.speed = prop_wrap("speed");

    }, "GeolocationSensor", [mod._Sensor]);

    sensor_factory("Accelerometer", mod._XYZSensor, SimpleAccelerometer);
    sensor_factory("Gyroscope", mod._XYZSensor, SimpleGyroscope);
    sensor_factory("Magnetometer", mod._XYZSensor, SimpleMagnetometer);
    sensor_factory("LinearAccelerationSensor", mod._XYZSensor, SimpleLinearAccelerationSensor);
    sensor_factory("GravitySensor", mod._XYZSensor, SimpleGravitySensor);
    sensor_factory("AbsoluteOrientationSensor", mod._OrientationSensor, SimpleAbsoluteOrientationSensor);
    sensor_factory("RelativeOrientationSensor", mod._OrientationSensor, SimpleRelativeOrientationSensor);

    return mod;
}
