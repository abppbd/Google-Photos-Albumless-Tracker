##chromedriver_path = "C:/Users/Me/Desktop/python with rclone/rclone_python/chrome-win64/chrome.exe"
##img_url = "https://photos.google.com/photo/AF1QipOte2UKzG3YFweMO9DhfpqMIvYOsTdI-f3LatSc"
##firefox_profile_path = "C:/Users/Me/AppData/Roaming/Mozilla/Firefox/Profiles/9j35egb3.default-release"
##geckodriver = "C:/Users/Me/Desktop/python with rclone/rclone_python/geckodriver.exe"


from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep, time
#from selenium.webdriver.support.wait import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains




#----------------------------------------------- LANCH THE CHROME DRIVER ---- #
def driver_init():
    # Initiate the driver.
    """
    Thanks to Panchdev Singh:
        https://stackoverflow.com/a/78148407
    """
    options = webdriver.ChromeOptions()

    options.add_argument("--disable-blink-features=AutomationControlled")
    # ^^ This ligne, single handedly, allows google photo log in :) ^^
    # (It doesn't throw the "not secure drowser, can't login" waning)
    
    #options.add_experimental_option("useAutomationExtension", False)
    #options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(options=options)
    #driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

# --------------------------------- MAKE USER LOGIN AND SELECT THE ALBUM ---- #
def goto_albums(driver):
    # Make the user login & select or create an album.
    # Get the album url from the link.

    driver.get("https://photos.google.com/albums")
    # Ask the albums page

    while "photos.google.com/albums" not in driver.current_url:
        # While the user hasn't signed in, the url domain will be:
        # "accounts.google.com", then the user will be reddirected.

        sleep(0.2)
        # Wait for the redirect.

    return True

# ----------------------------------------------------- GET THE ALBUM ID ---- #
def goto_albums(driver):
    # Find the ID of an album by parsing the url.

    url = driver.current_url()

    if "photos.google.com/album/" in url:
        album_id = url.replace("https://photos.google.com/album/", "")
        # Only keep the album ID:
        # https://photos.google.com/album/TheAlbumIDHere

        album_id = album_id.replace("/", "")
        # Remove the eventual final "/".

        return (True, album)

    # An album wasn't selected
    return (False, "The url doesn't point to an album, couldn't retrive the album ID")

# ------------------------------------------ CHECK FOR GOOGLE PHOTOS URL ---- #
def check_url(url):
    # Check is it's a google photos url.
    
    if "https://photos.google.com" not in url:
        # The links isn't for google photos.
        return "The web bot was given a non google photos url:\n" + url

    return True

# ------------------------------------------------------- GET URL ERRORS ---- #
def get_page_error(driver):
    # Check if there is a problem with the web page.

    head_title_xpath = "/html/head/title"
    head_title_elem = driver.find_element(By.XPATH, head_title_xpath)
    head_title = head_title_elem.get_attribute("innerHTML").loxer()
    # Retrive webpage title.

    if "error 404" in head_title:
        # Bad url.
        return "The 404 error for the requested page:\n" + driver.current_url

    if "can’t access photo" in head_title:
        # Wrong account.
        return "You are not logged in with the correct account, couldn't access the requested page:\n" + driver.current_url

    # Every thing went well.
    return True

#----------------------------------------------- OPEN ADD TOO ALBUM MENU ---- #
def open_album_menu(driver):
    # Open the "add to album" menu of the "more options" section.

    action = ActionChains(driver)
    # ActionChains used for the move_to_element method.

    try:
        more_options_xpath = "/html/body/div[1]/div/c-wiz/div[4]/c-wiz/div[1]/div[2]/div[2]/span/div/div[10]/div"
        # Full XPath to the "more options" button.
        more_option_elem = driver.find_element(By.XPATH, more_options_xpath)
        # "more options" element.
        action.move_to_element(more_option_elem).click().perform()
        # Find and click the "more options" button.

        sleep(0.4)
        # Wait for animation to finish.

    except NoSuchElementException:
        return "The \"more options\" button couldn't be found."

    try:
        add_to_album_xpath = "/html/body/div[6]/div/div/span[4]"
        # Full XPath to the "add to album" button.
        add_to_album_elem = driver.find_element(By.XPATH, add_to_album_xpath)
        # "add to album" element.
        action.move_to_element(add_to_album_elem).click().perform()
        # Find and click the "add to album" button.

    except NoSuchElementException:
        return "The \"Ad to album\" menu couldn't be opened."

    # Every thing went well.
    return True



#----------------------------------------------- WAIT FOR ELEMENT BY CSS ---- #
def wait_for_css(driver, css_selector, timeout=5, poll_frequency=0.1):
    # Wait for an elemnt to be available, visible and usable.
    # The wait is abandoned if it takes longer than the timeout in seconds.

    start = time()

    while time() - start < timeout:
        #While time's not up.

        try:
            element = driver.find_element(By.CSS_SELECTOR, css_selector)
            # The element exists.

            if element.is_displayed() and element.is_enabled():
                return element

            except NosuchElementException:
                # The element doesn't exists.
                pass

            sleep(poll_frequency)

            # Time's up !
            return False

#------------------------------------------ SELECT THE MOST RECENT ALBUM ---- #
def select_album_byID(driver, album_id):
    # Click on the album of the "add to album" menu, by album id.

    css_tag = f'data-id="{album_id}"'
    # CSS selector element used to find the album in the menu.

    album_elem = wait_for_css(driver, css_selector)
    # Wait for the album to be availble in the menu.

    if not album_elem:
        # Throw an error if the album wasn't found.
        return 'The desired album couldn\'t be found in the "add to album" menu.'

    action = ActionChains(driver)
    action.move_to_element(album_elem).click().perform()
    # Find and click the album from the menu.

    # Everything went well.
    return True

#------------------------------------------- ADD MEDIA TO ALBUM FROM URL ---- #
def add_to_album(driver, album_id, media_url):
    # To add a photo to an album w/ google photo (from 2024-07-17):
    # More options -> Add to album -> [select the album].

    media_url = media_url[:-1] if media_url[-1] == "/" else media_url
    # Allow redirect by removing the last "/" in the url.

    url_status = check_url(media_url)

    if url_status is not True:
        # Non google photos url, send error message.
        return url_status

    else:
        driver.get(media_url)
        # Open media page, redirected to google photo login.

    page_status = get_page_error(driver)

    if page_status is not True:
        # If there is a 404 error or an access denied, send error message.
        return page_status

    while "photos.google.com/photo/lr" in driver.current_url:
        # The media links are formed from the media ID:
        # https://photos.google.com/lr/photo/ID
        # And get redirected to the acctual media url:
        # https://photos.google.com/photo/AnotherID

        sleep(0.2)
        # Wait for the redirect

    open_album_menu_status = open_album_menu(driver)
    # Try to open the "add to album" menu.

    if open_album_menu_status is not True:
        # If the "add to album" menu couldn't be opened.
        return open_album_menu_status

    select_album_byID_status = select_album_byID(driver)
    # Try to add the media item to the desired album.

    if select_album_byID_status is not True:
        # If media couldn't be added to the album.
        return select_album_byID_status

    # Every thing went well
    return True

#-----------------------------------------------------------------------------#

def bulk_add_to_album(media_links):
    # Add all the Google photo's photos to an album.

    yield "Driver init"
    driver = driver_init()
    # Open chrome driver.

    yield "Album and login"
    album_init(driver, media_links)
    # Make user login & select/create the bulk album.

    add_to_album(driver, media_links)

    for media_link in media_links:
        pass

    yield driver

    #driver.quit()

#-----------------------------------------------------------------------------#

if __name__ == "__main__":
    driver = driver_init()
    album_init(driver, img_url)
    




"""
Thanks to undetected Selenium:
    https://stackoverflow.com/a/70134837

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from time import sleep


options = Options()
#options = webdriver.ChromeOptions()
#options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

#options.add_argument("start-minimized")

# Chrome is controlled by automated test software
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

s = Service(chromedriver_path)

driver = webdriver.Chrome(service=s, options=options)
#driver = webdriver.Chrome(options=options)

print("Shit")

# Selenium Stealth settings
stealth(driver,
      languages=["en-US", "en"],
      vendor="Google Inc.",
      platform="Win32",
      webgl_vendor="Intel Inc.",
      renderer="Intel Iris OpenGL Engine",
      fix_hairline=True,
  )
driver.get("https://www.google.com/photos/about/")
#driver.save_screenshot('bot_sannysoft.png')
"""
#-----------------------------------------------------------------------------#
"""
Thanks to Praveen Kumar:
    https://stackoverflow.com/a/67655204

from selenium import webdriver
from selenium_stealth import stealth

options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument('--disable-blink-features=AutomationControlled')
driver = webdriver.Chrome(options=options)
stealth(driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
    )
driver.get(img_url)
"""
#-----------------------------------------------------------------------------#
"""
Thanks to yusufusta:
    https://stackoverflow.com/a/66308429

Improved Thanks to Atanas Atanasov & 0xC0000022L:
    https://stackoverflow.com/a/69572816

from selenium import webdriver
#import geckodriver_autoinstaller
#from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium_stealth import stealth


# geckodriver_autoinstaller.install()

firefox_profile_path = "C:/Users/Me/AppData/Roaming/Mozilla/Firefox/Profiles/9j35egb3.default-release"
# https://support.mozilla.org/en-US/kb/profiles-where-firefox-stores-user-data

options=Options()
options.set_preference('profile', firefox_profile_path)

#options.set_preference("dom.webdriver.enabled", False)
#options.set_preference('useAutomationExtension', False)
#profile.update_preferences()
#desired = DesiredCapabilities.FIREFOX

service = Service("C:/Users/Me/Desktop/python with rclone/rclone_python/geckodriver.exe")

driver = Firefox(options=options)

print("good")

stealth(driver,
      languages=["en-US", "en"],
      vendor="Google Inc.",
      platform="Win32",
      webgl_vendor="Intel Inc.",
      renderer="Intel Iris OpenGL Engine",
      fix_hairline=True,
  )



driver.get(img_url)
"""
