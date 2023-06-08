import sys

from PyQt5.QtWidgets import QApplication
from analyser.AnalyserWindow import AnalyserWindow


def main():
    app = QApplication(sys.argv)
    ex = AnalyserWindow()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
