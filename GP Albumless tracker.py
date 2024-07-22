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
import traceback, sys

from rclone_python import rclone

from find_albumless_media import get_albumless_media

from add_to_album_web_bot import add_to_album, driver_init, album_init

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
    QListWidget,
    QPushButton,
    QTabWidget,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QWidget,
    QLabel,
    )








class Worker_get_remotes(QThread):
    # Use threads to don't lock up the UI while refreshing the remotes lists.

    finished = pyqtSignal()   # Finished signal.
    result = pyqtSignal(list) # Result signal.
    error = pyqtSignal(tuple) # Error signal.

    def __init__(self):
        super(Worker_get_remotes, self).__init__()

        

    @pyqtSlot()
    def run(self):

        if not rclone.is_installed():
            # No rclone
            self.finished.emit()
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
            self.finished.emit()
            # Done.







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
    # Refresh button when rclone config is changed.

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
    # TODO: add streatch so the list takes all the place.
    listing_layout.addWidget(listing["AddToAlbum"], stretch = 1)
    listing_layout.addLayout(batches_layout, stretch = 1)
    listing_layout.addWidget(listing["Continue"], stretch = 1)
    listing_layout.addWidget(listing["Help"], stretch = 1)

    return listing, listing_layout

# ------------------------------------------------- TEXT IN SELECTION HELP -- #
def get_selection_help():
    # Return the text for the help in the selection section.

    if not rclone.is_installed():
        # If rclone is not in the folder nor installed.
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


    elif rclone.get_remotes() == []:
        # If rclone has no remote(s).
        header = "\nHELP:\nIf you haven't created your remote:\n"
    else:
        # If rclone has remote(s).
        header = "\nHELP:\nTo create a new remote:\n"


    body = ("1) Open your CMD and go to this executable's directory:\n"
                f"\n\tcd {os.getcwd()}\n\n"
            "2) Create a new remote by typing:\n\n"
                "\trclone config\n\n"
            "3) Follow the instructions to create a new google photo remote.\n"
            "4) Comme back and hit Refresh.\n"
            "\n------------------------------\n"
            "Docs: https://rclone.org/googlephotos/")
    # Rclone new remote instruction.

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
                f"\trclone lsd {remote_name}album\n\n"
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




def error_shit(error = "No error, why is it called?"):
    print(error)


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

    # ---------------------------------------- UPDATE THE CURRENT REMOTE ---- #
    def update_remote(self, remote_name):
        self.remote = remote_name
        # Change remote

        self.Search["Search"].setText(
            "Search for albumless media in " + self.remote[:-1])
        # Update the Search button text (removed the trailing colon).
        
        self.Search["Help"].setText(get_search_help(self.remote))
        # Update the "Search" help section.

        if remote_name == "": # If remote name is empty.
            self.Search["Search"].setEnabled(False)
            # Disable search
        else: # If remote has a name.
            self.Search["Search"].setEnabled(True)
            # Enable search

##    # ----------------------------------------- UPDATE THEE REMOTES LIST ---- #
##    def refresh(self):
##        #======= Update tab 1 (selection) =======#
##        self.Selection["ComboBox"].clear()
##
##        if rclone.is_installed():
##            self.Selection["ComboBox"].addItems(rclone.get_remotes())
##        # Update list of remotes if rclone is installed.
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
##            # If no remotes are found or if rclone is unavalaible.
##
##            for i in range(1, self.tabs.count()):
##                self.tabs.setTabEnabled(i, False)
##            # Disable all the tabs except the 1st.
##
##
##        else: # If rclone is avalaible.
##
##            for i in range(1, self.tabs.count()):
##                self.tabs.setTabEnabled(i, True)
##            # Enable all the tabs
##
##            self.tabs.setCurrentIndex(0)
##            # Go to the 1st tab.

    # ----------------------------------------- UPDATE THEE REMOTES LIST ---- #
    def refresh(self):
        #======= Update tab 1 (selection) =======#
        self.Selection["ComboBox"].clear()

        self.refresh_thread = Worker_get_remotes()

        self.refresh_thread.result.connect(
            self.Selection["ComboBox"].addItems)

        self.refresh_thread.error.connect(error_shit)
        
        self.refresh_thread.start()
        # Get list of remotes without locking up the UI.
        print("TODO: Handle Errors !")
        print("TODO: Try inline worker result connect.")


        self.Selection["Help"].setText(get_selection_help())
        # Update the help section.

        #======== Update tab 2 (search) =========#
        # Handled by the self.remote_update() function.

        #============== UI Update ===============#
        if self.remote =="" or (not rclone.is_installed()):
            # If no remotes are found or if rclone is unavalaible.

            for i in range(1, self.tabs.count()):
                self.tabs.setTabEnabled(i, False)
            # Disable all the tabs except the 1st.


        else: # If rclone is avalaible.

            for i in range(1, self.tabs.count()):
                self.tabs.setTabEnabled(i, True)
            # Enable all the tabs

            self.tabs.setCurrentIndex(0)
            # Go to the 1st tab.

    # --------------------------------- SEARCH FOR ALBUMLESS MEDIA ITEMS ---- #
    def search_media(self):

        if not rclone.is_installed(): # If rclone is un avalaible
            self.refresh() # Refresh and
            return None    # exit.

        if self.remote == "" or self.remote not in rclone.get_remotes():
            # If there are no remotes or the current one is unavailable.
            self.refresh() # Refresh and
            return None    # exit.

        # Lock UI
        for i in range(self.tabs.count()):
                self.tabs.setTabEnabled(i, False)
        self.tabs.setCurrentIndex(1)
        # Stay on the 2nd tab.

        # Get Albumless media.

        def get_albumless_media_work(remote, ):
            for msg in get_albumless_media(self.remote):
                # Fetch get_albumless_media notification.
                if type(msg) == list:
                    # The last yielded element is a list of tuples containing the
                    # name and the url for every albumless media item.
                    #self.media_info = msg
                    return msg

                else:
                    progress_callback
                    # If yielded element isn't a list, it is a user message.
                    #self.Search["Status"].setText("Status: " + msg)
                    #self.repaint() # It's dirty, I know, -_-

        self.tabs.setCurrentIndex(2)
        # Go to the 3rd tab.

        self.repopulate_listing(self.media_info)
        # Fill the lists for the name & url for each albumless items.

        # Unlock UI
        for i in range(self.tabs.count()):
                self.tabs.setTabEnabled(i, True)

    # ----------------------------------------- SHOW USER ALBULESS MEDIA ---- #
    def repopulate_listing(self, media_info):
        # Put the names & links of the media items in the lists of tab 3.

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
        # TODO: add info

        self.Listing["Info"].setText("Info:\n\t"
                                     "Albumless media items count: "
                                     f"{total_count}\n\t"
                                     f"With a duplicate name: {dupe_count} "
                                     "(Item ID hidden)")

        if len(self.media_info) > 0:
            # If there are some albumless media items.
            self.Listing["AddToAlbum"].setEnabled(True)
            # Activate "add to album" button.



    def add_to_album_error(self, error):
        print(error)




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


    # ------------------------------------------------------ LOCK THE UI ---- #
    def lock_ui():
        current_tab = self.tabs.currentIndex()
        # Get the current tab index

        for i in range(1, self.tabs.count()):
                self.tabs.setTabEnabled(i, False)
        # Disable all the tabs

        current_tab = self.tabs.currentIndex()
        # Go back 
        






#=============================================================================#

if __name__ == "__main__":

    print("TODO: Setup refresh(), search() & addtoalbum() as worker threads.")

    
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
