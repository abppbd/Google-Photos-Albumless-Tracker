"""
This scripts creates an app that lists all the media items not in an album on
Google Photos and adds them to a "needs triage" album selected by the user.

The list of media items in google photo is fetched by python-rclone, based on
rClone: https://rclone.org/

The app is created with PyQt6, based on Qt v6: https://doc.qt.io/qt-6/

The items are added to the album with a webbot based on selenium:
https://www.selenium.dev/
"""

import os
import sys

from rclone_python import rclone
from time import sleep

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QStackedLayout,
    QApplication,
    QLabel,
    QComboBox,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QCheckBox,
    QSpinBox
    )


#-----------------------------------------------------------------------------#
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # Qt class subclassed, super __init__ call required.

        window_title = "Google Photos - Albumless to album"
        self.setWindowTitle(window_title)
        # Window setup.

        self.state = 0
        # 0 -> Set up state, everything is clickable.
        # 1 -> Searching, locked interface.
        # 2 -> Adding to album, locked interface.

        # Selection section:
        selection_layout = self.init_selection()
        # self.Selection = {
        #     "Title" : QLabel(),
        #     "ComboBox" : QComboBox(),
        #     "Refresh" : QPushButton(),
        #     "Help" : QLabel()
        #     }


        # Search Section
        self.Search = {
            "Title" : QLabel(),
            "Search" : QPushButton(),
            "Help" : QLabel()
            }

        self.Search["Title"].setText("2) Search for Albumless media.")
        self.Search["Title"].setFont(QFont("Arial", 20))

        self.Selection["Search"].setText(
            f"Search Remote: {self.Selection['ComboBox'].currentText()[:-1]}")







        self.Listing = {
            "Title" : QLabel(),
            "Table" : "Q?()",
            "AddToAlbum" : QPushButton(),
            "Is_batch" : QCheckBox(),
            "Batch_size" : QSpinBox()
            }


        main_layout = QStackedLayout()
        #main_layout.addWidget(remote_selection)

        central_widget = QWidget()
        central_widget.setLayout(selection_layout)
        self.setCentralWidget(central_widget)

#-----------------------------------------------------------------------------#
    def init_selection(self):
        # Set up selection section & it's layout.

        self.Selection = {
            "Title" : QLabel(),
            "ComboBox" : QComboBox(),
            "Refresh" : QPushButton(),
            "Help" : QLabel()
            }

        self.Selection["Title"].setText("1) Select the remote.")
        self.Selection["Title"].setFont(QFont("Arial", 20))

        self.Selection["ComboBox"].setEditable(False)
        self.update_combobox()
        # Add remotes to the ComboBox.

        self.Selection["Refresh"].setText("Refresh")
        self.Selection["Refresh"].clicked.connect(self.update_combobox)
        self.Selection["Refresh"].clicked.connect(self.selection_help)
        # When click refresh update ComboBox.

        self.Selection["Help"].setText("Add helpful text here")
        self.selection_help()
        # Add Help section

        combo_layout = QHBoxLayout()
        combo_layout.addWidget(self.Selection["ComboBox"])
        combo_layout.addWidget(self.Selection["Refresh"])
        # ComboBox/Refresh button layout

        selection_layout = QVBoxLayout()
        selection_layout.addWidget(self.Selection["Title"])
        selection_layout.addLayout(combo_layout)
        selection_layout.addWidget(self.Selection["Help"])
        # Selection section layout.

        return selection_layout

#-----------------------------------------------------------------------------#
    def update_combobox(self):
        # Update the list of remotes.

##        refresh_button = self.Selection["Refresh"]
        combobox = self.Selection["ComboBox"]

##        refresh_button.setEnabled(False)
##        refresh_button.setText("Fetching...")
##        # Update refresh button.

        combobox.clear()
        # Clear old remote list.

        if rclone.is_installed():
            # Avoid Exception error.
            combobox.addItems(rclone.get_remotes())
            # Add updated remote list.

##        refresh_button.setText("Refresh")
##        refresh_button.setEnabled(True)
##        # Update refresh button.

#-----------------------------------------------------------------------------#
    def selection_help(self):
        # Add the text in the help text field.

        self.Selection["Help"].setWordWrap(False)
        self.Selection["Help"].setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)


        if rclone.is_installed():
            text = ("HELP:\n"
                    "If you haven't created your remote:\n"
                    "1) Open your CMD and go to this executable's directory:\n"
                        f"\n\tcd {os.getcwd()}\n\n"
                    "2) Create a new remote by typing:\n\n"
                        "\trclone config\n\n"
                    "3) Follow the instructions to create a new remote.\n"
                    "4) Comme back and hit Refresh.\n\n"
                    "Docs: https://rclone.org/googlephotos/")
        else:
            # If rclone is not in the folder nor installed.
            text = ("HELP:\n"
                    "The rClone executable wasn't found in this executable's "
                    "directory nor in the %PATH% env variable:"
                    "\n1) Download rClone from:\n\n"
                        "\thttps://rclone.org/downloads/#release\n\n"
                    "2) Extract \"rclone.exe\" from the archive and place it "
                    "same folder:\n\n"
                        f"\t{os.getcwd()}\n\n"
                    "3) Comme back and hit Refresh.\n\n"
                    "Docs: https://rclone.org/install/#quickstart")

        self.Selection["Help"].setText(text)





def init_Search(self):
    pass





#-----------------------------------------------------------------------------#
if __name__ == "__main__":
        app = QApplication(sys.argv)

        window = MainWindow()
        window.show()

        app.exec()
