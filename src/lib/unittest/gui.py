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
            self.mydiv.setAttribute("id", self.divid + "_offscreen_unit_results")
            self.mydiv.setCSS("display", "none")
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
            self.resdiv.setAttribute("id", self.divid + "_unit_results")
            self.resdiv.setAttribute("class", "unittest-results")
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
            self.resdiv.setCSS("display", "none")

        headers = ["Result", "Actual Value", "Expected Value", "Notes"]
        row = document.createElement("tr")
        for item in headers:
            head = document.createElement("th")
            head.setAttribute("class", "ac-feedback")
            head.innerHTML = item
            head.setCSS("text-align", "center")
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
            errorData.setAttribute("class", "ac-feedback")
            errorData.innerHTML = "ERROR"
            errorData.setCSS("background-color", "#de8e96")
            errorData.setCSS("text-align", "center")
            row.appendChild(errorData)
        elif res:
            passed = document.createElement("td")
            passed.setAttribute("class", "ac-feedback")
            passed.innerHTML = "Pass"
            passed.setCSS("background-color", "#83d382")
            passed.setCSS("text-align", "center")
            row.appendChild(passed)
            self.numPassed += 1
        else:
            fail = document.createElement("td")
            fail.setAttribute("class", "ac-feedback")
            fail.innerHTML = "Fail"
            fail.setCSS("background-color", "#de8e96")
            fail.setCSS("text-align", "center")
            row.appendChild(fail)
            self.numFailed += 1

        act = document.createElement("td")
        act.setAttribute("class", "ac-feedback")
        if trimActual:
            actHTML = str(actual)[:5] + "..." + str(actual)[-5:]
            if actualType == str:
                actHTML = repr(actHTML)
            act.innerHTML = actHTML
        else:
            act.innerHTML = repr(actual)
        act.setCSS("text-align", "center")
        row.appendChild(act)

        expect = document.createElement("td")
        expect.setAttribute("class", "ac-feedback")

        if trimExpected:
            expectedHTML = str(expected)[:5] + "..." + str(expected)[-5:]
            if expectedType == str:
                expectedHTML = repr(expectedHTML)
            expect.innerHTML = expectedHTML
        else:
            expect.innerHTML = repr(expected)
        expect.setCSS("text-align", "center")
        row.appendChild(expect)
        inp = document.createElement("td")
        inp.setAttribute("class", "ac-feedback")

        if err:
            inp.innerHTML = msg
        else:
            inp.innerHTML = param
        inp.setCSS("text-align", "center")
        row.appendChild(inp)

        if trimActual or trimExpected:
            expandbutton = document.createElement("button")
            expandbutton.innerHTML = "Expand Differences"
            expandmsg = "Actual: " + str(actual) + "\nExpected: " + str(expected)
            expandbutton.setAttribute("value", expandmsg)
            expandbutton.setAttribute("type", "button")
            expandbutton.setAttribute("onclick", "alert(this.value)")
            expandbutton.setAttribute("class", "btn btn-info")
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
            jseval("window.edList['{}'].pct_correct = {}".format(self.closestDiv, pct))
            jseval(
                "window.edList['{}'].unit_results = '{}'".format(
                    self.closestDiv, pctcorrect
                )
            )
            jseval(
                "window.edList['{}'].unit_results_divid = '{}'".format(
                    self.closestDiv, self.mydiv.getAttribute("id")
                )
            )

        except:
            print(
                "failed to find object to record unittest results! {}".format(
                    pctcorrect
                )
            )
