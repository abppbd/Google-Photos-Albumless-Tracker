import traceback, sys
from time import time, sleep

from rclone_python import rclone

from find_albumless_media import get_albumless_media
from web_bot_functions import GP_web_bot

from PyQt6.QtCore import (
    pyqtSignal,
    pyqtSlot,
    QThread,
    QObject,
    QTimer,
    )

from PyQt6.QtWidgets import (
    QApplication,
    QWidget
    )

# ========================================================== THE REMOTES WORKER
class Worker_get_remotes(QObject):

    finished = pyqtSignal(bool) # Finished signal.
    result = pyqtSignal(list)   # Result signal.
    error = pyqtSignal(tuple)   # Error signal.

    def __init__(self, parent=None):
        super(Worker_get_remotes, self).__init__(parent)

    @pyqtSlot()
    def run(self):

        # Abort if there's no rClone.
        if not rclone.is_installed():
            self.finished.emit(False)
            return None

        # Get the list of remotes.
        try:
            remotes = rclone.get_remotes()

        # Handle errors.
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.error.emit((exctype, value, traceback.format_exc()))

        else:
            self.result.emit(remotes)

        finally:
            self.finished.emit(True)

    # Destroy worker.
    def close(self, *args, **kwargs):
        self.deleteLater()

# ==================================================== THE REMOTE SEARCH WORKER
class Worker_search(QObject):

    progress = pyqtSignal(str)  # User message signal.
    finished = pyqtSignal(bool) # Finished signal.
    result = pyqtSignal(list)   # Result signal.
    error = pyqtSignal(object)  # Error signal.

    def __init__(self, remote):
        super(Worker_search, self).__init__()

        self.remote = remote
        self.destroy = False

    @pyqtSlot()
    def run(self):

        # Get albumless media.
        try:
            for msg in get_albumless_media(self.remote):

                # Check if worker was interupted.
                QApplication.processEvents()
                if self.destroy:
                    self.finished.emit(False)
                    return

                # If yielded element is a string, it's a user message.
                if type(msg) == str:
                    self.progress.emit(msg)

                # The last yielded element is a list of tuples containing
                # the name and ID for every albumless media item.
                elif type(msg) == list:
                    media_info = msg

        # Handle errors.
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.error.emit((traceback.format_exc()))

        else:
            if not self.destroy:
                self.result.emit(media_info)

        finally:
            self.finished.emit(True)
            self.close()

    # Destroy worker.
    def close(self, *args, **kwargs):
        self.destroy = True
        self.deleteLater()


# ========================================================== THE WEB BOT WORKER
class Worker_web_bot(QObject):

    sig_album_id = pyqtSignal(object) # Album ID/Status signal.

    status = pyqtSignal(str)       # Current stat signal.
    sate_change = pyqtSignal(bool) # Pause/Resume signal.

    failed = pyqtSignal(tuple)   # Web bot fails signal
    finished = pyqtSignal(bool) # Finished signal.

    error = pyqtSignal(str) # Error signal.

    def __init__(self, media_IDs, driver=None):
        super().__init__()

        self.album_id = ""

        self.media_IDs = media_IDs

        self.progress = 0
        self.total = len(media_IDs)

        self.failed_url = []

        self.is_paused = True

        self.destroy = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.run_web_bot)

    # ----------------------------------------------------- INIT THE DRIVER
    @pyqtSlot()
    def run(self):

        # Open chromedriver.
        try:
            self.WB = GP_web_bot()
        except Exception as error:
            self.error.emit(str(error))
            return

        # Login & go to albums.
        self.WB.goto_albums()

        # Error msg.
        if self.WB.is_good is not True:
            self.error.emit(self.WB.is_good)

    # ------------------------------------------- UPDATE THE SELECTED ALBUM
    def select_album(self):

        # Fetch album id from url.
        try:
            get_id_status = self.WB.get_album_id()
        except Exception as error:
            self.error.emit(str(error))
            return

        # No album selected
        if get_id_status is not True:
            self.sig_album_id.emit(None)
            return None

        self.sig_album_id.emit(self.WB.album_id)

    # -------------------------------------------------- ADD MEDIA TO ALBUM
    def run_web_bot(self):

        # Get net item to add to album.
        media_ID = self.media_IDs[self.progress]
        media_url = f"https://photos.google.com/lr/photo/{media_ID}"

        self.status.emit(f"Now adding to the album the media:\n{media_url}")

        # Add item to album.
        try:
            add_to_album_status = self.WB.add_to_album(media_url)
        except Exception as error:
            self.error.emit(str(error))
            return
        finally:
            self.progress += 1

        # Log the failed add to album.
        if add_to_album_status is not True:
            self.status.emit(f"Couldn't add to the album the media:\n"
                             f"{media_url}\nBecause: {add_to_album_status}")
            self.failed_url.append((media_url, add_to_album_status))

        # Added everything, done.
        if self.progress == self.total - 1:
            if self.failed_url:
                self.failed.emit(tuple(self.failed_url))
            self.finished.emit(True)
            self.timer.stop()
            return None

        QApplication.processEvents()

        if self.destroy:
            self.finished.emit(True)
            try: self.driver.quit()
            except NameError:
                pass # Already deleted.
            return

        if not self.is_paused:
            self.timer.singleShot(100, self.run_web_bot)


    # ---------------------------------------------- START AND STOP WEB BOT
    def pause_toggle(self):
        # Pick up the work.
        if self.is_paused:
            self.is_paused = False
            self.run_web_bot()

        # Set the pause flag.
        else:
            self.is_paused = True

        self.sate_change.emit(self.is_paused)

    # --------------------------------------------------- SET UP END OF WEB BOT
    def schedule_destroy(self):
        self.destroy = True
        self.timer.stop()
        #self.timer.singleShot(100, self.terminate)

    # -------------------------------------------------------- KILL WEB BOT
    def close(self):

        self.timer.stop()

        start = time()

        # Wait 10s, give the web bot time to finish initiating.
        while time() - start < 10:
            # Try closing web driver.
            try:
                self.WB.close()
                break
            except AttributeError as error:
                # Web bot not finished initiating.
                pass

            sleep(0.5)

        if self.failed_url:
            self.failed.emit(tuple(self.failed_url))

        self.deleteLater()
