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

from rclone_python import rclone

from find_albumless_media import get_albumless_media

import add_to_album_web_bot as web_bot

from PyQt6.QtCore import (
    Qt,
    QThread,
    pyqtSignal,
    pyqtSlot,
    QThreadPool,
    QRunnable,
    QObject
    )

from PyQt6.QtGui import QFont

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,

    QHBoxLayout,
    QVBoxLayout,

    QAbstractItemView,
    QListWidgetItem,
    QErrorMessage,
    QMessageBox,
    QListWidget,
    QPushButton,
    QTabWidget,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QWidget,
    QLabel,
    )





def error_shit(error = "No error, why is it called?", parent=None):
    print("\nTODO: Handle Errors !")
    print(error)
##    error_dialog = QErrorMessage()
##    error_dialog.showMessage("Oh shit\n" + error)

    msg = QMessageBox()
    msg.critical(parent, "Error !", "An error has occured !\n" + str(error))










class Worker_get_remotes(QThread):
    # Use threads to don't lock up the UI while refreshing the remotes lists.

    finished = pyqtSignal(bool) # Finished signal.
    result = pyqtSignal(list)   # Result signal.
    error = pyqtSignal(tuple)   # Error signal.

    def __init__(self):
        super(Worker_get_remotes, self).__init__()

    @pyqtSlot()
    def run(self):

        if not rclone.is_installed():
            # No rClone
            self.finished.emit(False)
            # Stop.
            return None

        try:
            remotes = rclone.get_remotes()
            # Get the list of remotes

        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.error.emit((exctype, value, traceback.format_exc()))
            # Handle errors.

        else:
            self.result.emit(remotes)
            # "Return" the results.

        finally:
            self.finished.emit(True)
            # Done.


class Worker_search(QThread):
    # Use threads to don't lock up the UI while searching in the remote.

    progress = pyqtSignal(str)  # User message signal.
    finished = pyqtSignal(bool) # Finished signal.
    result = pyqtSignal(list)   # Result signal.
    error = pyqtSignal(object)   # Error signal.

    def __init__(self, remote):
        super(Worker_search, self).__init__()
        self.remote = remote

    @pyqtSlot()
    def run(self):

        try:
            for msg in get_albumless_media(self.remote):
                # Step throught the search.

                if type(msg) == str:
                    # If yielded element isn't a list, it's a user message.
                    self.progress.emit(msg)

                elif type(msg) == list:
                    # The last yielded element is a list of tuples containing
                    # the name and ID for every albumless media item.
                    media_info = msg

        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            print("type of the trace back:\n", type(traceback.format_exc()),
                  "\n", traceback.format_exc(), "\ndone.")
            self.error.emit((traceback.format_exc()))
            #self.error.emit((exctype, value, traceback.format_exc()))
            # Handle errors.

        else:
            self.result.emit(media_info)

        finally:
            self.finished.emit(True)
            # Done.


class Worker_add_media_batchless(QThread):
    # Use threads to don't lock up the UI while add items to album all at once.

    status = pyqtSignal(str)    # User message signal.
    help_str = pyqtSignal(str)  # Help step signal.
    finished = pyqtSignal(bool) # Finished signal.
    result = pyqtSignal(list)   # Result signal.
    error = pyqtSignal(object)   # Error signal.
    fail = pyqtSignal(list)     # Fail Signal.

    def __init__(self, url_list, nex_button):
        super(Worker_add_media_batchless, self).__init__()
        #self.driver = driver
        self.url_list = url_list
        self.next_button = nex_button
        self.album_id = ""
        self.url_fail = []
        # List of urls failed to add to album, and the cause.


    @pyqtSlot()
    def run(self):
        self.driver = driver_init()
        # Start the chrome driver.

        goto_albums(self.driver)
        # Open albums list.

        next_button.clicked.disconnect()
        next_button.clicked.connect(self.album_selected)
        # Repurpuse the button for album confirmation

    def album_selected(self):
        album_id_status = goto_albums(driver)
        # Make the user login & select/create an album.

        if album_id_status[0] is False:
            # Not a google photos album.

            error_shit(error = album_id_status[1])

            try: self.driver.quit()
            except NameError: pass
            # Close the driver if still opened.

            return None

        else:
            self.album_id = album_id_status[1]

        self.status.emit("Status:\n\tAlbum selected.")
        self.add_all()
        # Add all media to the album.



    def add_all(self):
        self.status.emit("Status:\n\tWeb bot running.")
        self.help_str.emit(get_listing_help(2))
        # Add to album, info for user.

        for media_url in self.url_list[1::]:
            # Step throught the url list.
            self.status.emit(f"Status:\n\tNow adding media url:\n\t"
                             "{media_url}\n\t"
                             "to the bulk album.")

            add_to_album_status = add_to_album(self.driver,
                                               self.album_id,
                                               self.media_url,)

            if add_to_album_status is not True:
                # Smth went wrong :/
                status_text = ("Status: /!\\ ERROR /!\\\n\t"
                               f"Failed to adding media url:\n\t"
                               "{media_url}\n\t"
                               "to the bulk album.\nCause:\n" +
                               add_to_album_status)

                self.status.emit(status_text)
                # User informed of fail.

                self.url_fail.append((media_url, add_to_album_status))
                # Keep fails.


        self.fail.emit(self.url_fail)
        # Media items not added to album.

        self.finished.emit(True)
        # Done.

        try: self.driver.quit()
        except NameError: pass
        # Close the driver if still opened.

##                album_init_status = album_init(driver, self.url_list[1])
##                # Use the 1st media item to init the album.
##
##                if album_init_status is not True:
##                    # Smth went wrong :/
##                    self.status.emit("Status: /!\\ ERROR /!\\\n\t" +
##                                     album_init_status)
##                    error_shit(album_ini_status)
##                    self.finished.emit(False)
##                    return None

##                while next_button.isDisabled():
##                    print("dodo")
##                    sleep(0.1)
##                    print("not dodo")
##                    # Wait for user to press next.

##                self.status.emit("Status:\n\tWeb bot running.")
##                self.help_str.emit(get_listing_help(2))
##                # Add to album, info for user.
##
##                for media_url in self.url_list[1::]:
##                    # Step throught the url list.
##                    self.status.emit(f"Status:\n\tNow adding media url:\n\t"
##                                     "{media_url}\n\t"
##                                     "to the bulk album.")
##                    add_to_album_status = add_to_album(driver, media_url)
##
##                    if add_to_album_status is not True:
##                        # Smth went wrong :/
##                        status_text = ("Status: /!\\ ERROR /!\\\n\t"
##                                       f"Failed to adding media url:\n\t"
##                                       "{media_url}\n\t"
##                                       "to the bulk album.\nCause:\n"
##                                       )#add_to_album_status)
##                        self.status.emit(status_text)
##                        # User informed of fail.
##                        url_fail.append((media_url, add_to_album_status))
##                        # Keep fail.

        except:
            traceback.print_exc()
            # Print error.

            exctype, value = sys.exc_info()[:2]
            self.error.emit((exctype, value, traceback.format_exc()))
            # Emit error error message box.

            


    


"""
    def add_to_album_batchless(self):
        links = [f"https://photos.google.com/lr/photo/" + i[1]
                 for i in self.media_info]
        #Get list of URLs.

        self.Listing["Help"].setText(get_listing_help(1))
        self.Listing["AddToAlbum"].setText("Next >")
        self.repaint() # It's dirty, I know, -_-

        with driver_init() as driver:
            # Initiate the chromium driver.
            # "with" automaticaly closes the driver if an error is thrown.

            album_init_status = album_init(driver, links[0])
            # Ask user to login & create/select the bulk album.

            print("ASK USER TO NOT COMPLETELY SQUISH THE WINDOW WHE RESIZING IT")

            while not self.Listing["AddToAlbum"].isDown():
                sleep(0.1)
                repaint() # It's dirty, I know, -_-
                self.processEvents()
            #input("Press enter when the album is created/selected (detect it!).")
            print("Next!")

            if album_init_status is not True:
                # If the album couldn't be initiated.
                self.add_to_album_error(album_init_status)
                return album_init_status

            for link in links[1::]:
                # Ignore the 1st link, added by user.
                add_to_album_status = add_to_album(driver, link)

                if add_to_album_status is not True:
                    # If the media item couldn't be added to the album.
                    self.add_to_album_error(add_to_album_status)
                    return add_to_album_status

        # Everything went well.
        return True
"""



# --------------------------------------------- INITIATE SELECTION SECTION -- #
def init_selection():
    # Set up selection section & it's layout.

    selection = {
        "Title" : QLabel(),
        "ComboBox" : QComboBox(),
        "Refresh" : QPushButton(),
        "Help" : QLabel()
        }

    selection["Title"].setText("1) Select the Google Photos remote.")
    selection["Title"].setFont(QFont("Arial", 20))
    # Section title setup.

    selection["ComboBox"].setEditable(False)
    # Only the program can add remotes names.

    selection["Refresh"].setText("Refresh")
    # Refresh button when rClone config is changed.

    selection["Help"].setText("Add helpful text here.")
    selection["Help"].setWordWrap(False)
    selection["Help"].setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse)
    # Add Help section.

    combo_layout = QHBoxLayout()
    combo_layout.addWidget(selection["ComboBox"], stretch = 2)
    combo_layout.addWidget(selection["Refresh"], stretch = 1)
    # ComboBox/Refresh button layout.

    selection_layout = QVBoxLayout()
    selection_layout.addWidget(selection["Title"], stretch = 1)
    selection_layout.addLayout(combo_layout, stretch = 1)
    selection_layout.addWidget(selection["Help"], stretch = 4)
    # Selection section layout.

    return selection, selection_layout

# ------------------------------------------------ INITIATE SEARCH SECTION -- #
def init_search():
    # Set up search section & it's layout.

    search = {
        "Title" : QLabel(),
        "Status" : QLabel(),
        "Search" : QPushButton(),
        "Help" : QLabel()
        }

    search["Title"].setText(
        "2) Search for Albumless media in Google Photos.")
    search["Title"].setFont(QFont("Arial", 20))
    # Section title setup.

    search["Status"].setText("Status: None")
    # Status label when searching remote.

    search["Help"].setText("Add helpful text here.")
    search["Help"].setWordWrap(False)
    search["Help"].setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse)
    # Add Help section.

    search_layout = QVBoxLayout()
    search_layout.addWidget(search["Title"], stretch = 1)
    search_layout.addWidget(search["Status"], stretch = 1)
    search_layout.addWidget(search["Search"], stretch = 1)
    search_layout.addWidget(search["Help"], stretch = 4)
    # Search section layout.

    return search, search_layout

# ----------------------------------------------- INITIATE LISTING SECTION -- #
def init_listing():
    # Set up listing (add to album) section & it's layout.

    listing = {
        "Title" : QLabel(),
        "Info" : QLabel(),
        "Name_label" : QLabel(),
        "Link_label" : QLabel(),
        "Name" : QListWidget(),
        "Link" : QListWidget(),
        "AddToAlbum" : QPushButton(),
        "Is_batch" : QCheckBox(),
        "Batch_size" : QSpinBox(),
        "Continue" : QPushButton(),
        "Status" : QLabel(),
        "Help": QLabel()
        }

    listing["Title"].setText("3) Add albumless media items in an album")
    listing["Title"].setFont(QFont("Arial", 20))
    # Section title setup.

    listing["Info"].setText("Info:\n\tNone")
    # Stats about found albumless media (amount, dup names...)

    listing["Name_label"].setText("Media name:")
    listing["Link_label"].setText("Google Photos media url:")
    # Add a fixed label for each list.

    listing["Name"].currentRowChanged.connect(listing["Link"].setCurrentRow)
    listing["Link"].currentRowChanged.connect(listing["Name"].setCurrentRow)
    # Sync up the two lists selections.

    vs_name = listing["Name"].verticalScrollBar()
    vs_link = listing["Link"].verticalScrollBar()
    # Get the lists' scroll bars
    vs_name.valueChanged.connect(vs_link.setValue)
    vs_link.valueChanged.connect(vs_name.setValue)
    # Sync up the two lists scrolls.

    listing["AddToAlbum"].setText("Add albumless items to a bulk album.")
    # Use the selenium web bot to add media items to an album.
    listing["AddToAlbum"].setEnabled(False)
    # The button will be enabled when media items will found.

    listing["Is_batch"].setText("(/!\\ Feature not implemented /!\\) "
                                "Add to album in batches of:")
    # Add media to album in batches.
    listing["Is_batch"].setEnabled(False)
    # Disabling the feature cuz it isn't ready.

    listing["Is_batch"].stateChanged.connect(
        listing["Batch_size"].setEnabled)
    listing["Is_batch"].stateChanged.connect(
        listing["Continue"].setEnabled)

    listing["Batch_size"].setSingleStep(100)
    listing["Batch_size"].setEnabled(listing["Is_batch"].isChecked())
    listing["Batch_size"].setMinimum(0)
    listing["Batch_size"].setMaximum(1000000000)
    listing["Batch_size"].setValue(100)
    # Use batch size if batches are used.

    listing["Continue"].setText("Process next batch >")
    listing["Continue"].setEnabled(listing["Is_batch"].isChecked())
    # Process the next batch of media items.

    nameList_layout = QVBoxLayout()
    nameList_layout.addWidget(listing["Name_label"])
    nameList_layout.addWidget(listing["Name"])
    # Names list layout.

    print("TODO: listing Status setup (add as selectable (link))")

    listing["Help"].setText("Add helpful text here.")
    listing["Help"].setWordWrap(True)
    listing["Help"].setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse)
    # Add Help section.

    linkList_layout = QVBoxLayout()
    linkList_layout.addWidget(listing["Link_label"])
    linkList_layout.addWidget(listing["Link"])
    # Links/URLs list layout.

    lists_layout = QHBoxLayout()
    lists_layout.addLayout(nameList_layout, stretch = 3)
    lists_layout.addLayout(linkList_layout, stretch = 4)
    # Both lists layout.

    batches_layout = QHBoxLayout()
    batches_layout.addWidget(listing["Is_batch"])
    batches_layout.addWidget(listing["Batch_size"])
    # Batches layout.

    listing_layout = QVBoxLayout()
    listing_layout.addWidget(listing["Title"], stretch = 1)
    listing_layout.addWidget(listing["Info"], stretch = 1)
    listing_layout.addLayout(lists_layout, stretch = 40)
    listing_layout.addWidget(listing["AddToAlbum"], stretch = 1)
    listing_layout.addLayout(batches_layout, stretch = 1)
    listing_layout.addWidget(listing["Continue"], stretch = 1)
    listing_layout.addWidget(listing["Help"], stretch = 1)

    return listing, listing_layout

# ------------------------------------------------- TEXT IN SELECTION HELP -- #
def get_selection_help():
    # Return the text for the help in the selection section.

    if not rclone.is_installed():
        # If rClone is not in the folder nor installed.
        text = ("\n/!\\ WARNING:\n"
                "The rClone executable wasn't found in this executable's "
                "directory nor in the %PATH% env variable:"
                "\n1) Download rClone from:\n\n"
                    "\thttps://rClone.org/downloads/#release\n\n"
                "2) Extract \"rClone.exe\" from the archive and place it "
                "same folder:\n\n"
                    f"\t{os.getcwd()}\n\n"
                "3) Comme back and hit Refresh.\n"
                "\n------------------------------\n"
                "Docs: https://rClone.org/install/#quickstart")
        return text


    elif rclone.get_remotes() == []:
        # If rClone has no remote(s).
        header = "\nHELP:\nIf you haven't created your remote:\n"
    else:
        # If rClone has remote(s).
        header = "\nHELP:\nTo create a new remote:\n"


    body = ("1) Open your CMD and go to this executable's directory:\n"
                f"\n\tcd {os.getcwd()}\n\n"
            "2) Create a new remote by typing:\n\n"
                "\trClone config\n\n"
            "3) Follow the instructions to create a new google photo remote.\n"
            "4) Comme back and hit Refresh.\n"
            "\n------------------------------\n"
            "Docs: https://rClone.org/googlephotos/")
    # rClone new remote instruction.

    return header+body

# ---------------------------------------------------- TEXT IN SEARCH HELP -- #
def get_search_help(remote_name):
    # Return the text for the help in the serch section.

    text = ("Searching takes a while, if the app doesn't respond, wait a "
            "bit and don't spam the button !\n\n\n"
            "HELP:\n"
            "If the search button does nothing or if the app crashes, it "
            "might indicate that the remote's access token is expired.\n"
            "To check if your access token is not expired:\n"
            "1) Open your CMD and go to this executable's directory:\n\n"
                f"\tcd {os.getcwd()}\n\n"
            "2) Run:\n\n"
                f"\trClone lsd {remote_name}album\n\n"
            "- If the token isn't expired you will see a list of your albums."
            "\n- If the token is expired you will recive a message saying so:"
            " Follow the instructions to recive a new token.")
    return text


def get_listing_help(step):
    # Help the user walk through.
    # Step 0: Driver initialisation, explain.
    # Step 1: Login Google Photo & select/create the bulk album.
    # Step 2: Instructions: Don't close the app & driver & don't resize driver.
    text = "HELP:\n"

    if step == 0:
        text += ("Due to limitations of the Google photos API , a web bot is "
                 "needed to to loop over every link and add the media to the "
                 "album like a regular user.")

    elif step == 1:
        text += ("In the chrome brwoser that opened up, log into your google "
                 "account.\n"
                 "Then, from the \"add to album\" menu popup, select/create "
                 "the album in which all the albumless media items will be "
                 "added.\n"
                 "Once finished press the \"Next >\" button.")
    elif step == 2:
        text += ("The web bot is now running.")

    text += ("\n\nIMPORTANT:\n" +
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
            "-" * 116)

    return text

# ---------------------------------------------- ADD WIDGET TO QLISTWIDGET -- #
def add_widget_to_list(QList, widget):
    # Add widgets to QListWidget:
    # https://stackoverflow.com/a/26199829

    listItem = QListWidgetItem()
    # Create an item for QListWidget.
    QList.addItem(listItem)
    # Add the QList item.
    QList.setItemWidget(listItem, widget)
    # Set the QList item to the widget.



# ============================================================ MAIN WINDOW == #
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # Qt class subclassed, super __init__ call required.

        # Window setup.
        window_title = "Google Photos - Albumless media tracker"
        self.setWindowTitle(window_title)

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        # Setup a threadpool to not lock up the UI.

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
        self.Listing["Help"].setText(get_listing_help(0))


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
    # ------------------------------------------------- CHECK FOR RCLONE ---- #
    def rclone_status(self):
        # Check if the rClone executable is availble.

        if rclone.is_installed():
            # rClone here, nothing to do.
            self.unlock_ui()
            return True

        # rClone not availble, lock all.
        self.tabs.setCurrentIndex(0) # Go to 1st tab.
        self.lock_ui()
        error_shit("The rclone executable couldn't be found or used.", self)
        return False

    # --------------------------------------- CHECK FOR GOOD REMOTE NAME ---- #
    def remote_status(self):
        # Check if it is all good for rClones calls.

        # rClone not availble, lock all.
        rclone_here = self.rclone_status()
        if not rclone_here:
            # Info for user.
            return False

        # No remotes, lock all.
        if self.remote == "":
            self.tabs.setCurrentIndex(0) # Go to 1st tab.
            self.lock_ui()
            error_shit("You have no remotes.", self)
            return False

        # Evreything ok.
        self.unlock_ui()
        self.Search["Search"].setEnabled(True)
        return True

    # ---------------------------------------- UPDATE THE CURRENT REMOTE ---- #
    def update_remote(self, remote_name):
        self.remote = remote_name
        # Change remote

        self.remote_status()
        # Verify rClone and remote name

        self.Search["Search"].setText(
            "Search for albumless media in " + self.remote[:-1])
        # Update the Search button text (removed the trailing colon).
        self.Search["Help"].setText(get_search_help(self.remote))
        # Update the "Search" help section.

    # ----------------------------------------- UPDATE THEE REMOTES LIST ---- #
    def refresh(self):
        
        def combobox_update(items):
            remote = self.remote
            # Keep remote name.

            self.Selection["ComboBox"].addItems(items)
            # Fill the combobox.

            index = self.Selection["ComboBox"].findText(remote)
            # Get new index of previous remote name (-1 if not found).
            if -1 < index < self.Selection["ComboBox"].count():
                # If index was found (>-1) and is selectable.
                self.Selection["ComboBox"].setCurrentIndex(index)
                # Go to previous remote's index.

        self.Selection["ComboBox"].blockSignals(True)
        self.Selection["ComboBox"].clear()
        self.Selection["ComboBox"].blockSignals(False)
        # Avoid UI updates while clearing.

        self.Selection["Help"].setText(get_selection_help())
        # Update the "Selection" help section.

        remote_here = self.rclone_status()

        # Stop the refresh if rClone not availble.
        if not remote_here:
            return None

        self.refresh_thread = Worker_get_remotes()
        # Thread to not lock up the UI.

        self.refresh_thread.result.connect(combobox_update)
        self.refresh_thread.error.connect(error_shit)
        # Handle results & errors.
            
        self.refresh_thread.start()
        # Get remotes

    # --------------------------------- SEARCH FOR ALBUMLESS MEDIA ITEMS ---- #
    def search_media(self):

        print("searching")

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

        self.search_thread = Worker_search(self.remote)

        self.search_thread.progress.connect(progress_message)
        self.search_thread.result.connect(media_info_fetched)
        self.search_thread.error.connect(error_shit)
        self.search_thread.error.connect(self.unlock_ui)
        self.search_thread.error.connect(self.refresh)

        self.search_thread.start()

        self.lock_ui()
        self.tabs.setTabEnabled(1, False)
        # Disable all to avoid button spam.

    # ----------------------------------------- SHOW USER ALBULESS MEDIA ---- #
    def repopulate_listing(self, media_info):
        # Put the names & links of the media items in the lists of tab 3.
        print("TODO: extract 'repopulate_listing' func from the class.")

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

            # -------------------------------- DUPPED ITEM NAMES ------------ #
            dupe_count += 1 if f"{{{ID}}}" in name else 0
            # Acount for dupped names of items.
            name = name.replace(f"{{{ID}}}", "") # WTF, 3 curly brackets !?
            # Remove ID in name for items w/ dupped names.

            # ------------------------------------- NAMES COLUMN ------------ #
            names_label = QLabel(name)
            # Get the name
            names_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse)
            # User can select the name.
            add_widget_to_list(self.Listing["Name"], names_label)
            # Add the name to the list.

            # -------------------------------------- URLs COLUMN ------------ #
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

        # ------------------------------------------ UPDATE INFO BOX -------- #
        self.Listing["Info"].setText("Info:\n\t"
                                     "Albumless media items count: "
                                     f"{total_count}\n\t"
                                     f"With a duplicate name: {dupe_count} "
                                     "(Item ID hidden)")

        if len(self.media_info) > 0:
            # If there are some albumless media items.
            self.Listing["AddToAlbum"].setEnabled(True)
            # Activate "add to album" button.


    def add_to_album_batchless(self):
        print("TODO: UI lock & unlock (add to album)")

        def add_to_album_done():
            print("reconect self.Listing['AddToAlbum'] the add to album func.")

        links = [f"https://photos.google.com/lr/photo/" + i[1]
                 for i in self.media_info]
        #Get list of URLs.

        self.Listing["Help"].setText(get_listing_help(1))
        self.Listing["AddToAlbum"].setText("Next >")
        self.repaint() # It's dirty, I know, -_-

        self.add_media_thread = Worker_add_media_batchless(
            links,
            nex_button = self.Listing["AddToAlbum"]
            )

        self.add_media_thread.help_str.connect(
            self.Listing["Help"].setText)
        self.add_media_thread.finished.connect(add_to_album_done)
        # Help section update.
        #self.add_media_thread.status.connect()
        # Keep user informed of status.
        #self.add_media_thread.fail.connect()
        # Show user failed add to album media items.
        self.add_media_thread.error.connect(error_shit)

        self.add_media_thread.start()

    # ------------------------------------------------------ LOCK THE UI ---- #
    def lock_ui(self, *args):
        current_tab = self.tabs.currentIndex()
        # Get the current tab index

        for i in range(self.tabs.count()):
            if i != current_tab:
                self.tabs.setTabEnabled(i, False)
                print("locked tab:", i)
        # Disable all the tabs except the current one.

        self.tabs.setCurrentIndex(current_tab)
        # Go back 

    # ---------------------------------------------------- UNLOCK THE UI ---- #
    def unlock_ui(self, *args):
        current_tab = self.tabs.currentIndex()
        # Get the current tab index

        for i in range(self.tabs.count()):
            self.tabs.setTabEnabled(i, True)
        # Enable all the tabs

        self.tabs.setCurrentIndex(current_tab)
        # Go back 
        






#=============================================================================#

if __name__ == "__main__":
    
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()







##    # ----------------------------------------- UPDATE THEE REMOTES LIST ---- #
##    def refresh(self):
##        #======= Update tab 1 (selection) =======#
##        self.Selection["ComboBox"].clear()
##
##        if rclone.is_installed():
##            self.Selection["ComboBox"].addItems(rclone.get_remotes())
##        # Update list of remotes if rClone is installed.
##
##        self.Selection["Help"].setText(get_selection_help())
##        # Update the help section.
##
##        #======== Update tab 2 (search) =========#
##        self.Search["Search"].setText(
##            "Search for albumless media in " + self.remote[:-1])
##        # Update the Search button text (removed the trailing colon).
##
##        self.Search["Help"].setText(get_search_help(self.remote))
##        # Update the help section.
##
##        #=============== Lock UI ================#
##        if self.remote =="" or (not rclone.is_installed()):
##            # If no remotes are found or if rClone is unavalaible.
##
##            for i in range(1, self.tabs.count()):
##                self.tabs.setTabEnabled(i, False)
##            # Disable all the tabs except the 1st.
##
##
##        else: # If rClone is avalaible.
##
##            for i in range(1, self.tabs.count()):
##                self.tabs.setTabEnabled(i, True)
##            # Enable all the tabs
##
##            self.tabs.setCurrentIndex(0)
##            # Go to the 1st tab.
