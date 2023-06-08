function $builtinmodule() {
    const {
        builtin: { str: pyStr },
        misceval: { callsimArray: pyCall },
        ffi: { toPy },
        abstr: { gattr },
    } = Sk;

    const documentMod = { __name__: new pyStr("document") };
    const documentProxy = toPy(Sk.global.document);

    Sk.abstr.setUpModuleMethods("document", documentMod, {
        __getattr__: {
            $meth(pyName) {
                return gattr(documentProxy, pyName, true);
            },
            $flags: { OneArg: true },
        },
        __dir__: {
            $meth() {
                return pyCall(documentProxy.tp$getattr(pyStr.$dir));
            },
            $flags: { NoArgs: true },
        },
    });

    documentMod.currentDiv = new Sk.builtin.func(function () {
        if (Sk.divid !== undefined) {
            return new Sk.builtin.str(Sk.divid);
        } else {
            throw new Sk.builtin.AttributeError(
                "There is no value set for divid"
            );
        }
    });

    documentMod.currentCourse = new Sk.builtin.func(function () {
        if (eBookConfig !== undefined) {
            return new Sk.builtin.str(eBookConfig.course);
        } else {
            throw new Sk.builtin.AttributeError("There is no course");
        }
    });

    documentMod.currentGradingContainer = new Sk.builtin.func(function () {
        if (Sk.gradeContainer !== undefined) {
            return new Sk.builtin.str(Sk.gradeContainer);
        } else {
            if (Sk.divid != undefined) {
                return new Sk.builtin.str(Sk.divid);
            }
            throw new Sk.builtin.AttributeError(
                "There is no value set for grading"
            );
        }
    });

    return documentMod;
}
