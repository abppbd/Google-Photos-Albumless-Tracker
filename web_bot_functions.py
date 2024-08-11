from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

from time import sleep, time

from PyQt6.QtCore import QObject


# ------------------------------------------------- CHECK FOR GOOGLE PHOTOS URL
def check_url(url):
    # Check is it's a google photos url.

    # The links isn't for google photos.
    if "https://photos.google.com" not in url:
        return "The web bot was given a non google photos url:\n" + url

    return True

# ======================================================= Google Photos Web Bot
class GP_web_bot(QObject):

    def __init__(self):
        super().__init__()

        self.driver_init()
        self.album_id = None
        self.is_good = True
        self.destroy = False

    # ----------------------------------------------------- LANCH THE CHROME DRIVER
    """
    Thanks to Panchdev Singh:
        https://stackoverflow.com/a/78148407
    """

    def driver_init(self):
        options = webdriver.ChromeOptions()

        # || This ligne, single handedly, allows google photo log in :) ||
        # \/    (Stops the "not secure drowser, can't login" waning)    \/
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Remove the "Choose your search engine" menu on driver launch.
        options.add_argument("--disable-search-engine-choice-screen")
        
        #options.add_experimental_option("useAutomationExtension", False)
        #options.add_experimental_option("excludeSwitches", ["enable-automation"])

        self.driver = webdriver.Chrome(options=options)
        #driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return True

    # ---------------------------------------- MAKE USER LOGIN AND SELECT THE ALBUM
    def goto_albums(self):
        # Go to albums, redirecting automaticaluy to google login page.

        try:
            self.driver.get("https://photos.google.com/albums")
        except Exception as error:
            # Keep track of error.
            self.is_good = error

        return True

    # ---------------------------------------------------- GET THE ALBUM ID
    def get_album_id(self):
        # Find the ID of an album by parsing the url.


        url = self.driver.current_url

        # https://photos.google.com/album/TheAlbumIDHere
        if "photos.google.com/album/" in url:

            # Get album ID and remove the eventual final "/".
            album_id = url.replace("https://photos.google.com/album/", "")
            album_id = album_id.replace("/", "")

            self.album_id = album_id

            return True

        # An album wasn't selected
        return "The url doesn't point to an album, couldn't retrive the album ID"

    # -------------------------------------------------------------- GET URL ERRORS
    def get_page_error(self):
        # Check if there is a problem with the web page.

        # Retrive webpage title.
        head_title_xpath = "/html/head/title"
        head_title_elem = self.driver.find_element(By.XPATH, head_title_xpath)
        head_title = head_title_elem.get_attribute("innerHTML").lower()

        # Bad url.
        if "error 404" in head_title:
            return "The 404 error for the requested page:\n" + self.driver.current_url

        # Wrong account.
        if "can’t access photo" in head_title:
            return "You are not logged in with the correct account, couldn't access the requested page:\n" + self.driver.current_url

        # Every thing went well.
        return True

    # --------------------------------------------------- WAIT FOR ELEMENT BY XPATH
    def wait_for_xpath(self, xpath, timeout=5, poll_frequency=0.5):
        # Wait for an elemnt to be available, visible and usable.
        # The wait is abandoned if it takes longer than the timeout in seconds.

        start = time()

        while time() - start < timeout:

            try:
                # The element exists.
                element = self.driver.find_element(By.XPATH, xpath)

                if element.is_displayed() and element.is_enabled():
                    return element

            # The element doesn't exists.
            except NoSuchElementException:
                pass

            sleep(poll_frequency)

        # Time's up !
        return False

    # --------------------------------------------- OPEN ADD TOO ALBUM MENU
    def open_album_menu(self):
        # Open the "add to album" menu from the "more options" section.

        # ActionChains for the move_to_element method.
        action = ActionChains(self.driver)

        # "more options" button full XPath.
        more_options_xpath = '//div[@aria-label="More options"][@__is_owner="true"]'#"/html/body/div[1]/div/c-wiz/div[4]/c-wiz/div[1]/div[2]/div[2]/span/div/div[10]/div"

        try:
            # "more options" element.
            more_option_elem = self.driver.find_element(
                By.XPATH, more_options_xpath)
        except NoSuchElementException:
            return "The \"more options\" button couldn't be found."

        # Find and click the "more options" button.
        action.move_to_element(more_option_elem).click().perform()
        # Wait for animation to finish.
        sleep(0.4)


        # "add to album" button full XPath.
        add_to_album_xpath = '//span[@aria-label="Add to album"]'#"/html/body/div[6]/div/div/span[4]"

        try:
            # "add to album" element.
            add_to_album_elem = self.driver.find_element(
                By.XPATH, add_to_album_xpath)
        except NoSuchElementException:
            return "The \"Ad to album\" menu couldn't be opened."

        # Find and click the "add to album" button.
        action.move_to_element(add_to_album_elem).click().perform()

        # Every thing went well.
        return True

    # ---------------------------------------- SELECT THE MOST RECENT ALBUM
    def select_album_byID(self):
        # Click on the album of the "add to album" menu by album id.

        # The XPATH to the selected album
        album_xpath = f'//li[@data-id="{self.album_id}"]'

        # Wait for the album to be availble in the menu.
        album_elem = self.wait_for_xpath(album_xpath)

        # Throw an error if the album wasn't found.
        if not album_elem:
            return 'The desired album couldn\'t be found in the "add to album" menu: ' + self.album_id

        # Find and click the album from the menu.
        action = ActionChains(self.driver)
        action.move_to_element(album_elem).click().perform()

        # Everything went well.
        return True

    # ----------------------------------------- ADD MEDIA TO ALBUM FROM URL
    def add_to_album(self, media_url):
        # To add a photo to an album w/ google photo (from 2024-07-17):
        # More options -> Add to album -> [select the album].

        # Remove last "/" to allow redirect.
        media_url = media_url[:-1] if media_url[-1] == "/" else media_url

        url_status = check_url(media_url)

        # Non google photos url, send error message.
        if url_status is not True:
            return url_status

        # Go to the media item's url.
        else:
            self.driver.get(media_url)

        page_status = self.get_page_error()

        # If there is a 404 error or an access denied, send error message.
        if page_status is not True:
            return page_status


        # The media links are formed from the media ID:
        # https://photos.google.com/lr/photo/ID
        # And get redirected to the acctual media url:
        # https://photos.google.com/photo/AnotherID
        while "photos.google.com/photo/lr" in self.driver.current_url:

            # Wait for the redirect
            sleep(0.1)

        # Try to open the "add to album" menu.
        open_album_menu_status = self.open_album_menu()

        # If the "add to album" menu couldn't be opened, send error msg.
        if open_album_menu_status is not True:
            return open_album_menu_status

        # Try to add the media item to the desired album.
        select_album_byID_status = self.select_album_byID()

        # If media couldn't be added to the album.
        if select_album_byID_status is not True:
            return select_album_byID_status

        # Every thing went well
        return True


    def close(self, *event):

        try:
            self.driver.quit()
        except AttributeError:
            # Web driver not created yet.
            pass

        self.deleteLater()
