"""
This scripts creates an app that lists all the media items not in an album on
Google Photos and adds them to a "needs triage" album selected by the user.

The list of media items in google photo is fetched by python-rClone, based on
rClone: https://rClone.org/

The app is created with PyQt6, based on Qt v6: https://doc.qt.io/qt-6/

The items are added to the album with a webbot based on selenium:
https://www.selenium.dev/
"""


import os
import traceback, sys
from time import sleep
from math import sqrt

from rclone_python import rclone

from workers import Worker_get_remotes, Worker_search
from web_bot_controller import web_bot_controller

from PyQt6.QtCore import (
    pyqtSignal,
    pyqtSlot,
    QThread,
    Qt,
    )
from PyQt6.QtGui import (
    QPalette,
    QFont,
    QIcon
    )
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,

    QHBoxLayout,
    QVBoxLayout,

    QListWidgetItem,
    QMessageBox,
    QListWidget,
    QPushButton,
    QTabWidget,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QWidget,
    QLabel,
    QStyle
    )

# Add the icon on the task bar.

def get_icon_path(window):

    # Get the window theme color.
    color = window.palette().color(QPalette.ColorRole(10))
    print("The Window color is", color.red(), color.green(), color.blue())

    """
    Brightness thanks to Darel Rex Finley:
        https://alienryderflex.com/hsp.html
    """
    brightness  =  sqrt(0.299 * color.red()**2 +
                        0.587 * color.green()**2 +
                        0.114 * color.blue()**2 )

    # Window QPalette is bright.
    if brightness > 127.5:
        icon_name = "GPAT light mode v2.ico"
        print("Using the light mode icon.")

    # Window QPalette is dark.
    else:
        icon_name = "GPAT dark mode v2.ico"
        print("Using the dark mode icon.")

    # Get the path to the ico file.
    cwd = os.getcwd()
    for folder, subfolders, files in os.walk(cwd):
        for f in files:
            if f == icon_name:
                return os.path.join(folder, f)

# --------------------------------------------------- ADD WIDGET TO QLISTWIDGET
def add_widget_to_list(QList, widget):
    """
    Add widgets to QListWidget, thanks to Jablonski & eric:
        https://stackoverflow.com/a/26199829
    """
    
    # Create an item for QListWidget.
    listItem = QListWidgetItem()

    # Add the QList item.
    QList.addItem(listItem)

    # Set the QList item to the widget.
    QList.setItemWidget(listItem, widget)

# ---------------------------------------------------------- ADD TO ALBUM FAILS
class web_bot_fail(QWidget):

    def __init__(self, fails = [], parent=None):
        super(web_bot_fail, self).__init__(parent)

        # Display QWidget as window despite being a child.
        self.setWindowFlags(Qt.WindowType(1))

        self.setWindowTitle("Media Items Fail")

        header = QLabel("Some media items couldn't be added to an album :")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)

        # Acknowledgement button.
        ok_b = QPushButton("OK")
        ok_b.setFixedWidth(100)
        ok_b.clicked.connect(self.close)

        # Tiles of the lists
        link_title = QLabel("Failed links :")
        cause_title = QLabel("Reason for Failure :")

        # Create the two list widgets.
        links_list = QListWidget()
        cause_list = QListWidget()

        # Sync up the two lists' selections.
        links_list.currentRowChanged.connect(cause_list.setCurrentRow)
        cause_list.currentRowChanged.connect(links_list.setCurrentRow)
        # Get and sync up the two lists' scrolls.
        vs_link = links_list.verticalScrollBar()
        vs_cause = cause_list.verticalScrollBar()
        vs_link.valueChanged.connect(vs_cause.setValue)
        vs_cause.valueChanged.connect(vs_link.setValue)

        # Fill the lists.
        for item in fails:
            link = item[0]
            cause = item[1]

            # Clickable link.
            link_label = QLabel()
            link_label.setOpenExternalLinks(True)
            link_label.setText(f"<a href={link}>{link}</a>")
            add_widget_to_list(links_list, link_label)

            # Selectable text.
            cause_label = QLabel(cause)
            add_widget_to_list(cause_list, cause_label)
            cause_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse)

        # Fit the links list to it's content plus 18 px for the scroll bar.
        links_list.setMaximumWidth(
            links_list.sizeHintForColumn(0) + 18)

        # Links layout
        link_lay = QVBoxLayout()
        link_lay.addWidget(link_title)
        link_lay.addWidget(links_list)

        # Causes layout
        cause_lay = QVBoxLayout()
        cause_lay.addWidget(cause_title)
        cause_lay.addWidget(cause_list)

        # Join the lists
        lists_layout = QHBoxLayout()
        lists_layout.addLayout(link_lay)
        lists_layout.addLayout(cause_lay)

        # Add all to the class widget.
        main_layout = QVBoxLayout()
        main_layout.addWidget(header)
        main_layout.addLayout(lists_layout)
        main_layout.addWidget(ok_b, alignment=Qt.AlignmentFlag.AlignRight)
        self.setLayout(main_layout)

        # Add the "/!\" icon.
        pixmap = QStyle.StandardPixmap.SP_MessageBoxWarning
        icon = self.style().standardIcon(pixmap)
        self.setWindowIcon(icon)

# ------------------------------------------------------------ ERROR DIALOG BOX
def error_shit(error = "No error, why is it called?", parent=None):
    print("\nAn error has occured:\n", "Error message Start:\n", error,
          "\nError message End.\n")

    msg = QMessageBox(parent=parent)
    pixmap = QStyle.StandardPixmap.SP_MessageBoxCritical
    icon = msg.style().standardIcon(pixmap)
    msg.setWindowIcon(icon)
    
    msg.critical(parent, "Error :/", "An error has occured :\n" + str(error))

# -------------------------------------------------- INITIATE SELECTION SECTION
def init_selection():
    # Set up selection section & it's layout.

    selection = {
        "Title" : QLabel(),
        "ComboBox" : QComboBox(),
        "Refresh" : QPushButton(),
        "Help" : QLabel()
        }

    # Section title setup.
    selection["Title"].setText("1) Select the Google Photos remote.")
    selection["Title"].setFont(QFont("Arial", 20))

    # Only the program can add remotes names.
    selection["ComboBox"].setEditable(False)

    # Refresh button when rClone config is changed.
    selection["Refresh"].setText("Refresh")

    # Add Help section.
    selection["Help"].setText("Add helpful text here.")
    selection["Help"].setWordWrap(False)
    selection["Help"].setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse)

    # ComboBox/Refresh button layout.
    combo_layout = QHBoxLayout()
    combo_layout.addWidget(selection["ComboBox"], stretch = 2)
    combo_layout.addWidget(selection["Refresh"], stretch = 1)

    # Selection section layout.
    selection_layout = QVBoxLayout()
    selection_layout.addWidget(selection["Title"], stretch = 1)
    selection_layout.addLayout(combo_layout, stretch = 1)
    selection_layout.addWidget(selection["Help"], stretch = 4)

    return selection, selection_layout

# ----------------------------------------------------- INITIATE SEARCH SECTION
def init_search():
    # Set up search section & it's layout.

    search = {
        "Title" : QLabel(),
        "Status" : QLabel(),
        "Search" : QPushButton(),
        "Help" : QLabel()
        }

    # Section title setup.
    search["Title"].setText(
        "2) Search for Albumless media in Google Photos.")
    search["Title"].setFont(QFont("Arial", 20))

    # Status label when searching remote.
    search["Status"].setText("Status: None")

    # Add Help section.
    search["Help"].setText("Add helpful text here.")
    search["Help"].setWordWrap(False)
    search["Help"].setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse)

    # Search section layout.
    search_layout = QVBoxLayout()
    search_layout.addWidget(search["Title"], stretch = 1)
    search_layout.addWidget(search["Status"], stretch = 1)
    search_layout.addWidget(search["Search"], stretch = 1)
    search_layout.addWidget(search["Help"], stretch = 4)

    return search, search_layout

# ---------------------------------------------------- INITIATE LISTING SECTION
def init_listing():

    listing = {
        "Title" : QLabel(),
        "Info" : QLabel(),
        "Name_label" : QLabel(),
        "Link_label" : QLabel(),
        "Name" : QListWidget(),
        "Link" : QListWidget(),
        "AddToAlbum" : QPushButton(),
        "Status" : QLabel(),
        "Help": QLabel()
        }

    # Section title setup.
    listing["Title"].setText("3) Add albumless media items in an album")
    listing["Title"].setFont(QFont("Arial", 20))

    # Stats about found albumless media (amount, dup names...)
    listing["Info"].setText("Info:\n\tNone")

    # Add a fixed label for each list.
    listing["Name_label"].setText("Media name:")
    listing["Link_label"].setText("Google Photos media url:")

    # Sync up the two lists selections.
    listing["Name"].currentRowChanged.connect(listing["Link"].setCurrentRow)
    listing["Link"].currentRowChanged.connect(listing["Name"].setCurrentRow)

    # Get the lists' scroll bars.
    vs_name = listing["Name"].verticalScrollBar()
    vs_link = listing["Link"].verticalScrollBar()

    # Sync up the two lists scrolls.
    vs_name.valueChanged.connect(vs_link.setValue)
    vs_link.valueChanged.connect(vs_name.setValue)

    # Use the selenium web bot to add media items to an album.
    # The button will be enabled when media items will found.
    listing["AddToAlbum"].setText("Open the Web Bot Controller")
    listing["AddToAlbum"].setEnabled(False)

    # Add status section.
    listing["Status"].setText("Status:\n\tNone")
    listing["Status"].setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse)

    # Add Help section.
    listing["Help"].setText("Add helpful text here.")
    listing["Help"].setWordWrap(True)
    listing["Help"].setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse)

    # Names list layout.
    nameList_layout = QVBoxLayout()
    nameList_layout.addWidget(listing["Name_label"])
    nameList_layout.addWidget(listing["Name"])

    # Links/URLs list layout.
    linkList_layout = QVBoxLayout()
    linkList_layout.addWidget(listing["Link_label"])
    linkList_layout.addWidget(listing["Link"])

    # Both lists layout.
    lists_layout = QHBoxLayout()
    lists_layout.addLayout(nameList_layout, stretch = 3)
    lists_layout.addLayout(linkList_layout, stretch = 4)

    # Final layout.
    listing_layout = QVBoxLayout()
    listing_layout.addWidget(listing["Title"], stretch = 1)
    listing_layout.addWidget(listing["Info"], stretch = 1)
    listing_layout.addLayout(lists_layout, stretch = 400) # list takes all.
    listing_layout.addWidget(listing["AddToAlbum"], stretch = 1)
    listing_layout.addWidget(listing["Status"], stretch = 1)
    listing_layout.addWidget(listing["Help"], stretch = 1)

    return listing, listing_layout

# ------------------------------------------------------ TEXT IN SELECTION HELP
def get_selection_help():

    # If rClone is not in the folder nor installed.
    if not rclone.is_installed():
        text = ("\n/!\\ WARNING:\n"
                "The rClone executable wasn't found in this executable's "
                "directory nor in the %PATH% env variable:"
                "\n1) Download rClone from:\n\n"
                    "\thttps://rclone.org/downloads/#release\n\n"
                "2) Extract \"rclone.exe\" from the archive and place it "
                "same folder:\n\n"
                    f"\t{os.getcwd()}\n\n"
                "3) Comme back and hit Refresh.\n"
                "\n------------------------------\n"
                "Docs: https://rclone.org/install/#quickstart")
        return text


    # If rClone has no remote(s).
    elif rclone.get_remotes() == []:
        header = "\nHELP:\nIf you haven't created your remote:\n"

    # If rClone has remote(s).
    else:
        header = "\nHELP:\nTo create a new remote:\n"


    # rClone new remote instruction.
    body = ("1) Open your CMD and go to this executable's directory:\n"
                f"\n\tcd {os.getcwd()}\n\n"
            "2) Create a new remote by typing:\n\n"
                "\trclone config\n\n"
            "3) Follow the instructions to create a new google photo remote.\n"
            "4) Comme back and hit Refresh.\n"
            "\n------------------------------\n"
            "Docs: https://rClone.org/googlephotos/")

    return header + body

# --------------------------------------------------------- TEXT IN SEARCH HELP
def get_search_help(remote_name):

    text = ("Searching takes a while, if the app doesn't respond, wait a "
            "bit and don't spam the button !\n\n\n"
            "HELP:\n"
            "If the search button does nothing or if the app crashes, it "
            "might indicate that the remote's access token is expired.\n"
            "To check if your access token is not expired:\n"
            "1) Open your CMD and go to this executable's directory:\n\n"
                f"\tcd {os.getcwd()}\n\n"
            "2) Run:\n\n"
                f"\trclone lsd {remote_name}album\n\n"
            "- If the token isn't expired you will see a list of your albums."
            "\n- If the token is expired you will recive a message saying so:"
            " Follow the instructions to recive a new token.")
    return text


def get_listing_help():
    # Help the user walk through.
    # Step 0: Driver initialisation, explain.
    # Step 1: Login Google Photo & select/create the bulk album.
    # Step 2: Instructions: Don't close the app & driver & don't resize driver.

    text = ("HELP:\n"
            "Due to limitations of the Google photos API , a web bot is "
            "needed to to loop over every link and add the media to the album "
            "like a regular user."

            "\n\nIMPORTANT:\n" +
            "-" * 116 + "\n"
            "/!\\\nWhile the web bot is running don't:\n"
            "- Click anywhere on the webpage.\n"
            "- Close, Minimize, or Resize the browser window."
            "- Move the window to a different desktop.\n"
            "- Switch to a different desktop\n\n"
            "While the web bot is running you can:\n"
            "- Press the \"Stop\" button or close the app to quit the browser."
            "\n- Move the browser window.\n"
            "- Hide the browser window with other apps and windows, letting "
            "it run in the background.\n"
            "/!\\\n" +
            "-" * 116
            )
    return text


# ========================================================== MAIN WINDOW ==== #
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # Qt class subclassed, super __init__ call required.

        print("GP Albumless tracker app Initiating...")

        # Set the appropriate taskbar icon depending on the theme.
        self.icon_path = get_icon_path(self)
        self.setWindowIcon(QIcon(self.icon_path))

        # Window setup.
        window_title = "Google Photos - Albumless media tracker"
        self.setWindowTitle(window_title)

        # Name of the currently selected remote.
        self.remote = ""

        # Tabs for the 3 steps: selection, search, add to album.
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setMovable(False)

        # Step 1: select the remote.
        self.Selection, selection_layout = init_selection()

        self.Selection["Refresh"].clicked.connect(self.refresh)
        self.Selection["ComboBox"].currentTextChanged.connect(
            self.update_remote)

        # Step 2: Search for albumless media.
        self.Search, search_layout = init_search()

        self.Search["Search"].clicked.connect(self.search_media)

        # Step 3: Add the albumless media to a single album.
        self.Listing, listing_layout = init_listing()

        self.Listing["AddToAlbum"].clicked.connect(self.add_to_album_batchless)
        self.Listing["Help"].setText(get_listing_help())


        # Add the "select remote" tab.
        selection_widget = QWidget()
        selection_widget.setLayout(selection_layout)
        self.tabs.addTab(selection_widget, "1 - Remote Selection ")

        # Add the "Search Albumless" tab.
        search_widget = QWidget()
        search_widget.setLayout(search_layout)
        self.tabs.addTab(search_widget, "2 - Search Albumless")

        # Add the "Add to Album" tab.
        listing_widget = QWidget()
        listing_widget.setLayout(listing_layout)
        self.tabs.addTab(listing_widget, "3 - Listing")

        # Load all.
        self.refresh()

        self.setCentralWidget(self.tabs)

    # ============================================ MAIN WINDOW FUNCTIONS ==== #
    # ---------------------------------------------------- CHECK FOR RCLONE
    def rclone_status(self):

        # rClone here, nothing to do.
        if rclone.is_installed():
            self.unlock_ui()
            return True

        # rClone not availble, lock all.
        self.tabs.setCurrentIndex(0) # Go to 1st tab.
        self.lock_ui((0,)) # Keep tab 1 unlocked.
        error_shit("The rcClone executable couldn't be found and/or used.", self)
        return False

    # ------------------------------------------ CHECK FOR GOOD REMOTE NAME
    def remote_status(self):

        # rClone not availble, lock all.
        rclone_here = self.rclone_status()
        if not rclone_here:
            return False

        # No remotes, lock all.
        if self.remote == "":
            self.tabs.setCurrentIndex(0) # Go to 1st tab.
            self.lock_ui((0,)) # Keep tab 1 unlocked.
            error_shit("You have no remotes.", self)
            return False

        # Evreything ok.
        self.unlock_ui()
        self.Search["Search"].setEnabled(True)
        return True

    # ------------------------------------------- UPDATE THE CURRENT REMOTE
    def update_remote(self, remote_name):

        # Change remote
        self.remote = remote_name

        print(f"Current remote updated: \"{self.remote}\"")

        # Verify rClone and remote name
        self.remote_status()

        # Update the Search button text (removed the trailing colon).
        self.Search["Search"].setText(
            "Search for albumless media in " + self.remote[:-1] + " >")

        # Update the "Search" help section.
        self.Search["Help"].setText(get_search_help(self.remote))

    # -------------------------------------------- UPDATE THEE REMOTES LIST
    def refresh(self):

        print("Refreshing the available remotes...")

        # Keep remote selected if it is in the new list.
        def combobox_update(items):
            old_remote = self.remote
            # Fill the combobox.
            self.Selection["ComboBox"].addItems(items)
            # Get new index of previous remote name (-1 if not found).
            index = self.Selection["ComboBox"].findText(old_remote)
            # If index was found (>-1) and is selectable.
            if -1 < index < self.Selection["ComboBox"].count():
                # Go to previous old_remote's index.
                self.Selection["ComboBox"].setCurrentIndex(index)

        # Avoid UI updates while clearing.
        self.Selection["ComboBox"].blockSignals(True)
        self.Selection["ComboBox"].clear()
        self.Selection["ComboBox"].blockSignals(False)

        # Update the "Selection" help section.
        self.Selection["Help"].setText(get_selection_help())

        # Stop the refresh if rClone not availble.
        remote_here = self.rclone_status()
        if not remote_here:
            return None

        # Init worker & thread
        self.refresh_thread = QThread()
        self.refresh_worker = Worker_get_remotes()
        self.refresh_worker.moveToThread(self.refresh_thread)
        self.refresh_thread.started.connect(self.refresh_worker.run)

        # Destroy worker & thread
        self.refresh_worker.finished.connect(self.refresh_worker.close)
        self.refresh_worker.finished.connect(self.refresh_thread.quit)

        # Handle results & errors.
        self.refresh_worker.result.connect(combobox_update)
        self.refresh_worker.error.connect(error_shit)

        self.refresh_thread.start()
        # Get remotes

    # ------------------------------------ SEARCH FOR ALBUMLESS MEDIA ITEMS
    def search_media(self):

        print("Searching for Albumless media items in remote...")

        if not rclone.is_installed(): # If rClone is un avalaible
            self.refresh() # Refresh and
            return None    # exit.

        if self.remote == "" or self.remote not in rclone.get_remotes():
            # If there are no remotes or the current one is unavailable.
            self.refresh() # Refresh and
            return None    # exit.

        # Get Albumless media.
        def progress_message(msg):
            self.Search["Status"].setText("Status:\n\t" + msg)

        def media_info_fetched(media_info):
            self.media_info = media_info
            self.tabs.setCurrentIndex(2)
            # Go to the 3rd tab.
            self.repopulate_listing(self.media_info)
            # Fill the lists for the name & url for each albumless items.
            self.unlock_ui()

        # Init worker & thread.
        self.search_thread = QThread()
        self.search_worker = Worker_search(self.remote)
        self.search_worker.moveToThread(self.search_thread)
        self.search_thread.started.connect(self.search_worker.run)

        # Destroy worker & thread.
        self.search_worker.finished.connect(self.search_worker.deleteLater)
        self.search_worker.finished.connect(self.search_thread.quit)

        #Handle worker's events.
        self.search_worker.progress.connect(progress_message)
        self.search_worker.result.connect(media_info_fetched)
        self.search_worker.finished.connect(
            lambda: self.unlock_ui())
        self.search_worker.error.connect(self.unlock_ui)
        self.search_worker.error.connect(self.refresh)
        self.search_worker.error.connect(error_shit)

        self.search_thread.start()

        self.lock_ui()
        # Disable all to avoid button spam.

    # -------------------------------------------- SHOW USER ALBULESS MEDIA
    def repopulate_listing(self, media_info):
        # Put the names & links of the media items in the lists of tab 3.

        self.media_info = media_info

        self.Listing["Name"].clear()
        self.Listing["Link"].clear()
        # Clear lists

        dupe_count = 0
        total_count = len(media_info)

        for i in media_info:
            # Loop over every media items.

            name = i[0]
            ID = i[1]
            url = f"https://photos.google.com/lr/photo/{ID}"

            # ----------------------------------- DUPPED ITEM NAMES
            dupe_count += 1 if f"{{{ID}}}" in name else 0
            # Acount for dupped names of items.
            name = name.replace(f"{{{ID}}}", "") # WTF, 3 curly brackets !?
            # Remove ID in name for items w/ dupped names.

            # ---------------------------------------- NAMES COLUMN
            names_label = QLabel(name)
            # Get the name
            names_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse)
            # User can select the name.
            add_widget_to_list(self.Listing["Name"], names_label)
            # Add the name to the list.

            # ----------------------------------------- URLs COLUMN
            urls_label = QLabel(url)
            # Get the google photos url.
            urls_label.setOpenExternalLinks(True)
            urls_label.setText(f"<a href={url}>{url}</a>")
            # User can click the links.
            add_widget_to_list(self.Listing["Link"], urls_label)
            # Add the url to the list.

        self.Listing["Link"].setMaximumWidth(
            self.Listing["Link"].sizeHintForColumn(0))
        # Fit the links list to it's content.

        # --------------------------------------------- UPDATE INFO BOX
        self.Listing["Info"].setText("Info:\n\t"
                                     "Albumless media items count: "
                                     f"{total_count}\n\t"
                                     f"With a duplicate name: {dupe_count} "
                                     "(Item ID hidden)")

        if len(self.media_info) > 0:
            # If there are some albumless media items.
            self.Listing["AddToAlbum"].setEnabled(True)
            # Activate "add to album" button.

        else:
            # If there arn't albumless media items.
            self.Listing["AddToAlbum"].setEnabled(False)
            error_shit(error="No albumless media items were found.")


    # ------------------------------------------------------- START WEB BOT
    def add_to_album_batchless(self):

        print("Starting the Web Bot Controller...")

        self.Listing["AddToAlbum"].setEnabled(False)

        # List of URLs from IDs.
        media_id = [i[1] for i in self.media_info]

        # Open the web bot.
        self.add_media_worker = web_bot_controller(
            parent=self, media_IDs=media_id, icon_path=self.icon_path)

        self.add_media_worker.show()

        self.add_media_worker.finished.connect(
            self.add_media_worker.close)


        # Handle web bot controller events.
        self.add_media_worker.finished.connect(
            lambda: self.Listing["AddToAlbum"].setEnabled(True))
        self.add_media_worker.error.connect(error_shit)

        def display_failed_url(fail=[]):
            self.fail_window = web_bot_fail(fail, self)
            self.fail_window.show()
        self.add_media_worker.failed.connect(display_failed_url)

    # --------------------------------------------------------- LOCK THE UI
    def lock_ui(self, whitelist=()):
        current_tab = self.tabs.currentIndex()
        # Get the current tab index

        for i in range(self.tabs.count()):
            if i not in whitelist:
                self.tabs.setTabEnabled(i, False)
        # Disable all the tabs except the current one.

        self.tabs.setCurrentIndex(current_tab)
        # Go back 

    # ------------------------------------------------------- UNLOCK THE UI
    def unlock_ui(self, *args):
        current_tab = self.tabs.currentIndex()
        # Get the current tab index

        for i in range(self.tabs.count()):
            self.tabs.setTabEnabled(i, True)
        # Enable all the tabs

        self.tabs.setCurrentIndex(current_tab)
        # Go back


    def closeEvent(self, event):

        # --------------------------------------------- KILL REFRESH WORKER
        try:
            self.refresh_worker.close()
        except (RuntimeError, AttributeError) as error:
            # Refresh worker not yet created or already deleted.
            pass

        try:
            self.refresh_thread.quit()
            self.refresh_thread.wait()
        except AttributeError as error:
            # Refresh thread not yet created.
            pass

        # ---------------------------------------------- KILL SEARCH WORKER
        try:
            self.search_worker.close()
        except (RuntimeError, AttributeError) as error:
            # Refresh worker not yet created or already deleted.
            pass

        try:
            self.search_thread.quit()
            self.search_thread.wait()
        except AttributeError as error:
            # Refresh thread not yet created.
            pass

        # ---------------------------------------- KILL ADD TO ALBUM WORKER
        #                                                         (Web Bot)
        try:
            self.add_media_worker.close()
        # Web bot controller not yet created.
        except AttributeError as error:
            pass

        # Inherit QMainWindow closing event.
        super(MainWindow, self).closeEvent(event)


# =========================================================================== #
if __name__ == "__main__":
    
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
