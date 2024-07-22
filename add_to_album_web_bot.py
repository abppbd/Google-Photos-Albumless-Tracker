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
    
    #options.add_experimental_option("useAutomationExtension", False)
    #options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(options=options)
    #driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

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
        return "The \"more options\" menu couldn't be opened."

    # Every thing went well.
    return True

#-------------------------------------------- MAKE USER SELECT THE ALBUM ---- #
def album_init(driver, media_url):
    # Make the user login & select or create an album.

    media_url = media_url[:-1] if media_url[-1] == "/" else media_url
    # Allow redirect (for login) by removing the last "/" in the url.

    driver.get(media_url)
    # Open media page, redirected to google photo login.

    while "photos.google.com/photo/" not in driver.current_url:
        # The media links are formed from the media ID:
        # https://photos.google.com/lr/photo/ID
        # And get redirected to the acctual media url:
        # https://photos.google.com/photo/AnotherID
        sleep(0.5)
        # Wait for the redirect

    open_album_menu_status = open_album_menu(driver)
    # Try to open the "add to album" menu.

    if open_album_menu_status is not True:
        # If the "add to album" menu couldn't be opened.
        return open_album_menu_status

    # Every thing went well.
    return True

#--------------------------------------------- WAIT FOR ELEMENT BY XPATH ---- #
def wait_for_xpath(driver, xpath, timeout=5, poll_frequency=0.1):
    # Wait for an elemnt to be available, visible and usable.
    # The wait is abandoned if it takes longer than the timeout in seconds.

    start = time()

    while time() - start < timeout:
        # While time's not up

        try:
            element = driver.find_element(By.XPATH, xpath)
            # The element exists.
            if element.is_displayed() and element.is_enabled():
                # The element is visible and can be used.
                return element

        except NoSuchElementException:
            # The element doesn't exist.
            pass

        sleep(poll_frequency)

    # Time's up !
    return False

#------------------------------------------ SELECT THE MOST RECENT ALBUM ---- #
def add_to_recent_album(driver):
    # Click on the top, most recent album of the "add to album" menu.

    top_album_xpath = "/html/body/div[2]/div/div[2]/div[2]/div/div/div/div[2]/div/ul/div[1]/li[1]"
    # Full XPath to the clickable top album of the "recent" section in the
    # "add to album" menu.
    top_album_elem = wait_for_xpath(driver, top_album_xpath)
    # Wait for "add to album" menu to be availble.

    if not top_album_elem:
        # Exit if the top album element wasn't found
        return "The top album of the \"recent\" section in the \"add to album\" menu couldn't be found."
    
    action = ActionChains(driver)
    action.move_to_element(top_album_elem).click().perform()
    # Find and click the album button.

    return True

#------------------------------------------- ADD MEDIA TO ALBUM FROM URL ---- #
def add_to_album(driver, media_url):
    # To add a photo to an album w/ google photo (from 2024-07-17):
    # More options -> Add to album -> [select most recent album].

    media_url = media_url[:-1] if media_url[-1] == "/" else media_url
    # Allow redirect (for login) by removing the last "/" in the url.

    driver.get(media_url)
    # Go to the photo's actual url.

    while "photos.google.com/photo/" not in driver.current_url:
        # The media links are formed from the media ID:
        # https://photos.google.com/lr/photo/ID
        # And get redirected to the acctual media url:
        # https://photos.google.com/photo/AnotherID
        sleep(0.5)
        # Wait for the redirect

    open_album_menu_status = open_album_menu(driver)
    # Try to open the "add to album" menu.

    if open_album_menu_status is not True:
        # If the "add to album" menu couldn't be opened.
        return open_album_menu_status

    add_to_recent_album_status = add_to_recent_album(driver)
    # Try to add the media item to the most recent album.

    if add_to_recent_album_status is not True:
        # If media couldn't be added to the album.
        return add_to_recent_album_status

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
