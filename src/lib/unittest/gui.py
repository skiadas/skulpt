import document
from unittest import TestCase
from urllib.request import urlopen
from time import sleep


class TestCaseGui(TestCase):
    def __init__(self):
        TestCase.__init__(self)
        self.closestDiv = document.currentDiv()
        self.divid = document.currentGradingContainer()
        self.mydiv = document.getElementById(self.divid)
        # If there is no div then create a dummy to avoid errors when running
        # grading "off screen"
        if self.mydiv is None:
            self.mydiv = document.createElement("div")
            self.mydiv.id = self.divid + "_offscreen_unit_results"
            self.mydiv.style.display = "none"
            body = document.getElementsByTagName("body")[0]
            body.appendChild(self.mydiv)
            self.unit_results_divid = self.divid + "_offscreen_unit_results"

        res = document.getElementById(self.divid + "_unit_results")
        if res:
            self.resdiv = res
            res.innerHTML = ""
            self.unit_results_divid = self.divid + "_unit_results"
        else:
            self.resdiv = document.createElement("div")
            self.resdiv.id = self.divid + "_unit_results"
            self.resdiv.classList.add("unittest-results")
            self.mydiv.appendChild(self.resdiv)
            self.unit_results_divid = self.divid + "_unit_results"

    def main(self):
        t = document.createElement("table")
        self.resTable = t
        x = self.resdiv.closest(".timedComponent")
        if x:
            self.is_timed = True
        else:
            self.is_timed = False
        self.resdiv.appendChild(self.resTable)
        if self.is_timed:
            self.resdiv.style.display = "none"

        headers = ["Result", "Actual Value", "Expected Value", "Notes"]
        row = document.createElement("tr")
        for item in headers:
            head = document.createElement("th")
            head.classList.add("ac-feedback")
            head.innerHTML = item
            head.style.textAlign = "center"
            row.appendChild(head)
        self.resTable.appendChild(row)

        for func in self.tlist:
            try:
                self.setUp()
                func()
                self.tearDown()
            except Exception as e:
                self.appendResult("Error", None, None, str(e).split("on line")[0])
                self.numFailed += 1
        self.showSummary()

    def getOutput(self):
        sleep(0.2)
        # self.divid will be the gradingWrapper when in grading mode
        if self.closestDiv != self.divid:
            output = document.querySelector(
                "#{} #{}_stdout".format(self.divid, self.closestDiv)
            )
        else:
            output = document.getElementById(self.divid + "_stdout")
        return output.innerText

    def getEditorText(self):
        return document.getCurrentEditorValue()

    def appendResult(self, res, actual, expected, param):
        trimActual = False
        if len(str(actual)) > 15:
            trimActual = True
            actualType = type(actual)
        trimExpected = False
        if len(str(expected)) > 15:
            trimExpected = True
            expectedType = type(expected)
        row = document.createElement("tr")
        err = False
        if res == "Error":
            err = True
            msg = "Error: %s" % param
            errorData = document.createElement("td")
            errorData.classList.add("ac-feedback")
            errorData.innerHTML = "ERROR"
            errorData.style.backgroundColor = "#de8e96"
            errorData.style.textAlign = "center"
            row.appendChild(errorData)
        elif res:
            passed = document.createElement("td")
            passed.classList.add("ac-feedback")
            passed.innerHTML = "Pass"
            passed.style.backgroundColor = "#83d382"
            passed.style.textAlign = "center"
            row.appendChild(passed)
            self.numPassed += 1
        else:
            fail = document.createElement("td")
            fail.classList.add("ac-feedback")
            fail.innerHTML = "Fail"
            fail.style.backgroundColor = "#de8e96"
            fail.style.textAlign = "center"
            row.appendChild(fail)
            self.numFailed += 1

        act = document.createElement("td")
        act.classList.add("ac-feedback")
        if trimActual:
            actHTML = str(actual)[:5] + "..." + str(actual)[-5:]
            if actualType == str:
                actHTML = repr(actHTML)
            act.innerHTML = actHTML
        else:
            act.innerHTML = repr(actual)
        act.style.textAlign = "center"
        row.appendChild(act)

        expect = document.createElement("td")
        expect.classList.add("ac-feedback")

        if trimExpected:
            expectedHTML = str(expected)[:5] + "..." + str(expected)[-5:]
            if expectedType == str:
                expectedHTML = repr(expectedHTML)
            expect.innerHTML = expectedHTML
        else:
            expect.innerHTML = repr(expected)
        expect.style.textAlign = "center"
        row.appendChild(expect)
        inp = document.createElement("td")
        inp.classList.add("ac-feedback")

        if err:
            inp.innerHTML = msg
        else:
            inp.innerHTML = param
        inp.style.textAlign = "center"
        row.appendChild(inp)

        def foo(evt):
            document.popup(expandmsg)

        if trimActual or trimExpected:
            expandbutton = document.createElement("button")
            expandbutton.innerHTML = "Expand Differences"
            expandmsg = "Actual: " + str(actual) + "\nExpected: " + str(expected)
            expandbutton.value = expandmsg
            expandbutton.type = "button"
            expandbutton.addEventListener("click", foo)
            expandbutton.classList.add("btn", "btn-info")
            row.appendChild(expandbutton)

        self.resTable.appendChild(row)

    def showSummary(self):
        pct = float(self.numPassed) / (self.numPassed + self.numFailed) * 100
        pctcorrect = (
            "percent:"
            + str(pct)
            + ":passed:"
            + str(self.numPassed)
            + ":failed:"
            + str(self.numFailed)
        )
        pTag = document.createElement("p")
        if not self.is_timed:
            pTag.innerHTML = "You passed: " + str(pct) + "% of the tests"
            self.resdiv.appendChild(pTag)
        try:
            jseval(
                "window.componentMap['{}'].pct_correct = {}".format(
                    self.closestDiv, pct
                )
            )
            jseval(
                "window.componentMap['{}'].unit_results = '{}'".format(
                    self.closestDiv, pctcorrect
                )
            )
            jseval(
                "window.componentMap['{}'].unit_results_divid = '{}'".format(
                    self.closestDiv, self.mydiv.getAttribute("id")
                )
            )

        except:
            print(
                "failed to find object to record unittest results! {}".format(
                    pctcorrect
                )
            )
