#from PyQt6.QtGui import *

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QApplication,
    QVBoxLayout,
    QLabel,
    QPushButton
    )

from PyQt6.QtCore import (
    QThread,
    pyqtSignal,
    QObject,
    QThreadPool,
    QTimer,
    QRunnable,
    pyqtSlot
    )

from time import sleep
import traceback, sys



##class Worker(QRunnable):
##    '''
##    Worker thread
##
##    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
##
##    :param callback: The function callback to run on this worker thread. Supplied args and
##                     kwargs will be passed through to the runner.
##    :type callback: function
##    :param args: Arguments to pass to the callback function
##    :param kwargs: Keywords to pass to the callback function
##
##    '''
##
##    def __init__(self, fn, *args, **kwargs):
##        super(Worker, self).__init__()
##
##        # Store constructor arguments (re-used for processing)
##        self.fn = fn
##        self.args = args
##        self.kwargs = kwargs
##        self.signals = WorkerSignals()
##
##        # Add the callback to our kwargs
##        self.kwargs['progress_callback'] = self.signals.progress
##
##    @pyqtSlot()
##    def run(self):
##        '''
##        Initialise the runner function with passed args, kwargs.
##        '''
##
##        # Retrieve args/kwargs here; and fire processing using them
##        try:
##            result = self.fn(*self.args, **self.kwargs)
##        except:
##            traceback.print_exc()
##            exctype, value = sys.exc_info()[:2]
##            self.signals.error.emit((exctype, value, traceback.format_exc()))
##        else:
##            self.signals.result.emit(result)  # Return the result of the processing
##        finally:
##            self.signals.finished.emit()  # Done


class Worker(QThread):

    progress = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        for i in range(5):
            self.progress.emit(f"this is the loop number {i}.")
            sleep(1)


class MainWindow(QMainWindow):


    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.counter = 0

        layout = QVBoxLayout()

        self.l = QLabel("Start")
        b = QPushButton("DANGER!")
        b.pressed.connect(self.oh_no)

        layout.addWidget(self.l)
        layout.addWidget(b)

        w = QWidget()
        w.setLayout(layout)

        self.setCentralWidget(w)

        self.show()

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()

    def oh_no(self):
        # Pass the function to execute
        self.working = Worker() # Any other args, kwargs are passed to the run function
        self.working.progress.connect(self.going)

        # Execute
        self.working.start()

    #pyqtSlot(str)
    def going(self, progress=""):
        print("the function said:", progress)
        #self.processEvents()


    def recurring_timer(self):
        self.counter +=1
        self.l.setText("Counter: %d" % self.counter)


app = QApplication([])
window = MainWindow()
app.exec()
