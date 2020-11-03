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
        res = document.getElementById(self.divid + "_unit_results")
        if res:
            self.resdiv = res
            res.innerHTML = ""
        else:
            self.resdiv = document.createElement("div")
            self.resdiv.setAttribute("id", self.divid + "_unit_results")
            self.resdiv.setAttribute("class", "unittest-results")
            self.mydiv.appendChild(self.resdiv)

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
            self.resdiv.setCSS('display','none')

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
            expandbutton.setAttribute("onclick", "alert(this.value)")
            expandbutton.setAttribute("class", "btn btn-info")
            row.appendChild(expandbutton)

        self.resTable.appendChild(row)

    def showSummary(self):
        pct = float(self.numPassed) / (self.numPassed + self.numFailed) * 100
        pTag = document.createElement("p")
        if not self.is_timed:
            pTag.innerHTML = "You passed: " + str(pct) + "% of the tests"
            self.resdiv.appendChild(pTag)
        else:
            # This is a little hacky
            try:
                jseval("window.edList['{}'].pct_correct = {}".format(self.closestDiv, pct))
            except:
                print("failed to find object to record unittest results - they are on the server")

        pctcorrect = (
            "percent:"
            + str(pct)
            + ":passed:"
            + str(self.numPassed)
            + ":failed:"
            + str(self.numFailed)
        )
        course = document.currentCourse()
        if jseval("Sk.logResults"):
            urlopen(
                "/runestone/ajax/hsblog",
                "event=unittest&div_id="
                + self.divid
                + "&act="
                + pctcorrect
                + "&course="
                + course,
            )
