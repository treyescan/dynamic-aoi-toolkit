from PyQt5.QtCore import QRect, QThreadPool
from PyQt5.QtWidgets import QWidget, QPushButton, QProgressBar, QListView, QAbstractItemView, QLabel, QLineEdit
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from analyser.AnalyseWorker import AnalyseWorker
import sys, glob, re
from datetime import datetime

sys.path.append('../../')
import __constants

input_folder = __constants.input_folder

class AnalyserWindow(QWidget):
    total = 0
    done = 0

    def __init__(self):
        super().__init__()

        self.initUI()  # init the UI

    def initUI(self):
        self.setWindowTitle('Treyescan GP x AOI Analyser')

        self.resize(502, 278)

        self.fetchButton = QPushButton('Fetch files to analyse', self)
        self.fetchButton.setGeometry(QRect(20, 20, 181, 26))
        self.fetchButton.clicked.connect(self.fetchFilesToAnalyse)

        self.analyseButton = QPushButton('Start analysis', self)
        self.analyseButton.setGeometry(QRect(20, 50, 181, 26))
        self.analyseButton.clicked.connect(self.analyseFiles)

        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(QRect(220, 20, 151, 23))
        self.progressBar.setValue(0)

        self.progressLabel = QLabel(self)
        self.progressLabel.setGeometry(QRect(381, 20, 201, 23))
        self.progressLabel.setText("(0/0) 0%")

        self.threadsLabel = QLabel(self)
        self.threadsLabel.setGeometry(QRect(20, 100, 181, 20))
        self.threadsLabel.setText("Threads: 0")

        self.startedLabel = QLabel(self)
        self.startedLabel.setGeometry(QRect(20, 120, 181, 20))
        self.startedLabel.setText("Started: not yet started")

        self.finishedLabel = QLabel(self)
        self.finishedLabel.setGeometry(QRect(20, 140, 181, 20))
        self.finishedLabel.setText("Finished: not yet finished")

        self.batchLabel = QLabel(self)
        self.batchLabel.setGeometry(QRect(20, 180, 181, 20))
        self.batchLabel.setText("Batch ID:")

        self.batchIDInput = QLineEdit(self)
        self.batchIDInput.setGeometry(QRect(20, 210, 181, 20))

        self.listView = QListView(self)
        self.listView.setGeometry(QRect(220, 50, 256, 192))
        self.model = QStandardItemModel()
        self.listView.setModel(self.model)
        self.listView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.show()

    def fetchFilesToAnalyse(self):
        participants_to_analyse = glob.glob(
            "{}/*/*/*/gaze_positions_on_surface_Surface1WB.csv".format(input_folder))
        
        self.total = len(participants_to_analyse)
        self.progressLabel.setText(f"(0/{self.total}) 0%")

        for i, file in enumerate(participants_to_analyse):
            regex = re.findall("(P-[0-9]..)\/(T[0-9])\/([a-zA-Z0-9]*)", file)

            participant_id = regex[0][0]
            measurement_moment = regex[0][1]
            task_id = regex[0][2]
        
            item = QStandardItem("%s, %s, %s, %s" % (i, participant_id, measurement_moment, task_id))

            self.model.appendRow(item)

    def analyseFiles(self):
        count = self.model.rowCount()

        if(count == 0):
            self.fetchFilesToAnalyse()
        
        count = self.model.rowCount()

        self.analyseButton.setDisabled(True)
        self.fetchButton.setDisabled(True)

        self.threadpool = QThreadPool()
        # self.threadpool.setMaxThreadCount(count)
        self.threadpool.setMaxThreadCount(8)
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.threadsLabel.setText(f"Threads: {self.threadpool.maxThreadCount()}")

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        self.startedLabel.setText(f"Started: {current_time}")

        for i in range(count):
            index = self.model.index(i, 0)
            row = index.data(0)

            # Make a new worker for the file we fetched
            analyse_worker = AnalyseWorker(row, self.batchIDInput.text())
            analyse_worker.signals.started.connect(self.startedAnalysis)
            analyse_worker.signals.finished.connect(self.finishedAnalysis)
            analyse_worker.signals.error.connect(self.errorAnalysis)
            self.threadpool.start(analyse_worker)

    def startedAnalysis(self, row_id):
        index = self.model.index(int(row_id), 0)
        row = index.data(0)
        self.model.setData(index, f"{row} 🕐")

    def errorAnalysis(self, row_id):
        index = self.model.index(int(row_id), 0)
        row = index.data(0)
        self.model.setData(index, f"{row} ❌".replace("🕐", ""))
        self.updateProgressIndicators()

    def finishedAnalysis(self, row_id):
        index = self.model.index(int(row_id), 0)
        row = index.data(0)
        self.model.setData(index, f"{row} ✅".replace("🕐", ""))
        self.updateProgressIndicators()

    def updateProgressIndicators(self):
        self.done = self.done + 1
        percentage = round(self.done / self.total * 100)
        self.progressBar.setValue(percentage)

        self.progressLabel.setText(f"({self.done}/{self.total}) {percentage}%")

        if(percentage == 100):
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            self.finishedLabel.setText(f"Finished: {current_time}")