from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QTextEdit,
    QVBoxLayout,
    QPushButton,
)
from PySide6.QtCore import Qt
from functools import partial

class PyCalc:
    def __init__(self, model, view):
        self._evaluate = model
        self._view = view
        self._connectSignalsAndSlots()

    def _calculateResult(self):
        result = self._evaluate(expression=self._view.getresultBoxContent())
        self._view.setresultBoxContent(result)

    def _buildExpression(self, subExpression):
        if "Error" in self._view.getresultBoxContent():
            self._view.clearDisplay()
        expression = self._view.getresultBoxContent() + subExpression
        self._view.setresultBoxContent(expression)

    def _connectSignalsAndSlots(self):
        for keySymbol, button in self._view.buttonMap.items():
            if keySymbol not in {"=", "C"}:
                button.clicked.connect(
                    partial(self._buildExpression, keySymbol)
                )
        self._view.buttonMap["="].clicked.connect(self._calculateResult)
        self._view.buttonMap["C"].clicked.connect(self._view.clearDisplay)


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.buttonsLayout = QGridLayout()

        self.addResultBox()
        self.addButtons()

        PyCalc(model=self.evaluateExpression, view=self)

        self.setLayout(self.layout)
    
    def addResultBox(self):
        self.resultBox = QTextEdit("")
        self.resultBox.setStyleSheet("font-size: 35px;")
        self.resultBox.setReadOnly(True)
        self.resultBox.setMinimumHeight(90)

        self.layout.addWidget(self.resultBox)

    def addButtons(self):
        self.buttonMap = {}

        keyBoard = [
            ["1", "2", "3", "/", "C"],
            ["4", "5", "6", "*", "("],
            ["7", "8", "9", "-", ")"],
            ["00", "0", ".", "+", "="],
        ]

        for row, keys in enumerate(keyBoard):
            for col, key in enumerate(keys):
                self.buttonMap[key] = QPushButton(key)
                self.buttonMap[key].setMinimumSize(40, 60)
                self.buttonMap[key].setStyleSheet("font-size: 20px;")
                self.buttonsLayout.addWidget(self.buttonMap[key], row, col)

        self.layout.addLayout(self.buttonsLayout)
    
    def setresultBoxContent(self, text):
        self.resultBox.setText(text)
        self.resultBox.setFocus()

    def getresultBoxContent(self):
        return self.resultBox.toPlainText()

    def clearDisplay(self):
        self.resultBox.setText("")

    def evaluateExpression(self, expression):
        try:
            result = str(eval(expression, {}, {}))
        except ZeroDivisionError:
            result = "Error: Division by Zero"
        except Exception:
            result = "Error"
        return result