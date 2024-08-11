"""
This script creates a small app to control the Google photos web bot.

+-------------------------+
| § W-B_C         _  ¤  X |
+-------------------------+
|  +-------------------+  |
|  |1) Select the Album|  |
|  +-------------------+  |
|  +-------------------+  |
|  |       2) GO       |  |
|  +-------------------+  |
|  +-------------------+  |
|  |       Kill        |  |
|  +-------------------+  |
|                         |
|  Help, Status & junk.   |
|                         |
+-------------------------+
"""
import sys
from time import sleep, time

from workers import Worker_web_bot as web_bot

from PyQt6.QtCore import (
    pyqtSignal,
    pyqtSlot,
    QThread,
    Qt
    )
from PyQt6.QtGui import (
    QIcon
    )
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,

    QVBoxLayout,

    QPushButton,
    QWidget,
    QLabel,
    )


# Display errors.
def error_shit(error = "No error, why is it called?", parent=None):
    print("\nAn error has occured:\n", "Error message Start:\n", error,
          "\nError message End.\n")

    msg = QMessageBox()
    pixmap = QStyle.StandardPixmap.SP_MessageBoxCritical
    icon = msg.style().standardIcon(pixmap)
    msg.setWindowIcon(icon)

    msg.critical(parent, "Error !", "An error has occured !\n" + str(error))


# ========================================================== WEB BOT CONTROLLER
class web_bot_controller(QMainWindow):

    failed = pyqtSignal(tuple)

    finished = pyqtSignal(bool)
    error = pyqtSignal(object)

    def __init__(self, parent=None, media_IDs=(), icon_path=None):
        super().__init__()

        self.icon_path = icon_path

        self.media_IDs = media_IDs
        self.album_id = None

        self.UI_init()
        self.web_bot_init()

        self.WB_status = None

    # ----------------------------------------------------- INIT THE WINDOW
    def  UI_init(self):
        # Window setup.
        window_title = "WebBot Controller"
        self.setWindowTitle(window_title)

        # Set the appropriate taskbar depending on the theme.
        self.setWindowIcon(QIcon(self.icon_path))

        # Select the ALbum.
        self.select_album_b = QPushButton("2) Select the Album")
        #self.select_album_b.clicked.connect(self.select_album)

        # Start the web bot.
        self.go_b = QPushButton("3) Go")
        self.go_b.setEnabled(False)
        self.go_b.clicked.connect(self.press_pause)

        # Kill the web bot
        self.kill_b = QPushButton("Kill")
        self.kill_b.clicked.connect(self.close)

        # Help section.
        self.help = QLabel("A bit of help.")
        help_txt = (
            "Help:\n\t"
            "1) Log into your google account.\n\t"
            "2) Go into your \"needs triage\" album or create it.\n\t\t"
            "(You can change the selected album)\n\t"
            "3) Once satisfied start the web bot with the button \"Go\"\n\n\t"
            "You can pause and resume the web bot with the same button.\n\t"
            "While paused, you can change the designated album.\n\t"
            "(When paused the web bot might take up to 10s to stop, don't spam !)\n"
            "\nIMPORTANT:\n"
            "/!\\\nWhile the web bot is running don't:\n"
            "- Click anywhere on the webpage.\n"
            "- Close, Minimize, or Resize the browser window.\n"
            "- Move the window to a different desktop.\n"
            "- Switch to a different desktop.\n\n"
            "While the web bot is running you can:\n"
            "- Press the \"Kill\" button or close the app to quit the browser."
            "\n- Move the browser window.\n"
            "- Hide the browser window with other apps and windows, letting "
            "it run in the background.\n"
            "/!\\\n"
            )
        self.help.setText(help_txt)

        # Status section.
        status_title = QLabel("\n\nStatus:")
        self.status = QLabel("None.")
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)

        # All the layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.select_album_b)
        main_layout.addWidget(self.go_b)
        main_layout.addWidget(self.kill_b)
        main_layout.addWidget(self.help)
        main_layout.addWidget(status_title)
        main_layout.addWidget(self.status)

        central_wid = QWidget()
        central_wid.setLayout(main_layout)
        self.setCentralWidget(central_wid)

    # --------------------------------------------- INTI THE WEB BOT THREAD
    @pyqtSlot()
    def web_bot_init(self):

        # Init the thread & the worker.
        self.thread = QThread()
        self.worker = web_bot(media_IDs=self.media_IDs)

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker.close)
        self.worker.finished.connect(self.thread.quit)

        # Connect the UI to the web bot.
        self.select_album_b.clicked.connect(self.worker.select_album)
        self.kill_b.clicked.connect(self.worker.close)
        self.go_b.clicked.connect(self.worker.pause_toggle)

        # Connect the web bot's events.
        self.worker.sig_album_id.connect(self.update_album_id)
        self.worker.status.connect(self.status.setText)
        self.worker.sate_change.connect(lambda: self.go_b.setEnabled(True))
        self.worker.failed.connect(self.failed.emit)
        self.worker.error.connect(error_shit)
        self.worker.error.connect(self.close)

        # Start thread
        self.thread.start()

    # ---------------------------------------------- START AND STOP WEB BOT
    def press_pause(self):
        # Prevent spam.
        self.go_b.setEnabled(False)

        # Pause the web bot.
        if self.WB_status == "Running":
            self.status.setText("The web bot has been paused")
            self.WB_status = "Paused"
            self.go_b.setText("Resume")
            self.select_album_b.setEnabled(True)

        # Resume the web bot.
        elif self.WB_status == "Paused" or self.WB_status is None:
            self.status.setText("The web bot has been resumed")
            self.WB_status = "Running"
            self.go_b.setText("Pause")
            self.select_album_b.setEnabled(False)

    # ------------------------------------------- CHANGE THE SELECTED ALBUM
    def update_album_id(self, album_id):
        # User not in an album.
        if album_id is None:
            self.status.setText(f"You are not in an album, the previously selected album will be used:\nhttps://photos.google.com/album/{self.album_id}")

        # New album.
        elif album_id != self.album_id:
            self.album_id = album_id
            self.status.setText(f"Updated the selected album to:\nhttps://photos.google.com/album/{self.album_id}")

        # Album unchanged.
        elif album_id == self.album_id:
            self.status.setText(f"The same album selected:\nhttps://photos.google.com/album/{self.album_id}")

        # Block start until album aquired.
        if self.album_id != None and self.WB_status is None:
            self.go_b.setEnabled(True)

    # ----------------------------------------------------- KILL EVERYTHING
    def closeEvent(self, event):

        try:
            self.worker.schedule_destroy()
            self.worker.close()
        except (RuntimeError, AttributeError) as error:
            # Worker not yet created or already deleted.
            pass

        try:
            self.thread.quit()
            self.thread.wait()
        except (RuntimeError, AttributeError) as error:
            # Thread not yet created or already deleted.
            pass

        super(web_bot_controller, self).closeEvent(event)

