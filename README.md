# What is Google Photos Albumless Tracker (GPAT) ?
With [Google Photos (GP)](https://photos.google.com/) you can create albums to organize your media items (photos, videos...). But you can't easily find the unorganized ones mindlessly floating in your Google Photos aether !

_Google Photos Albumless Tracker_ is a GUI based app that finds albumless media, and adds them to a "needs triage album" with a web bot.

<sup>You can the app run from the bare python script or from the executable bundle, instructions bellow</sup>

- [From the Python scripts](#from-the-python-script)
  - [Requirements](#requirements)
  - [Download](#download)
  - [Running](#running)
- [From the EXE build](#from-the-exe-build)
  - [Requirements](#requirements-1)
  - [Download](#download-1)
  - [Running](#running-1)
- [Usage](usage)
- [Info & Credits](#info--credits)
- [Possible Failure Points](possible-failure-points)


# From the python script
## Requirements
The scripts where written and tested with [Python 3.12.4](https://www.python.org/downloads/release/python-3124/).

### Packages
Before running the script you will need to install some packages:
- [PyQt6](https://pypi.org/project/PyQt6) for the GUI.
  ```bash
  pip install PyQt6
  ```
- [selenium](https://pypi.org/project/selenium/) for the web bot.
  ```bash
  pip install selenium
  ```
- [rclone-python](https://pypi.org/project/rclone-python) to interact with GP API.
  ```bash
  pip install rclone-python
  ```

### rClone
The rclone-python package uses [rClone](https://rclone.org/) which should be downloaded.
- (Recommended) For the satandalone executable, go to [rClone downloads](https://rclone.org/downloads), download the appropriate one for your device, and put it in the same folder as the python scripts. <sub>(tested with _GPAT_)</sub>
- To install it on your machine, go to [rClone install](https://rclone.org/install) and follow the instructions. <sub>(/!\ not tested with _GPAT_ /!\\)</sub>

You will have to create a "remote" to your Google Photos account, [follow the instructions with "rclone config"](https://rclone.org/googlephotos/#configuration).

## Download
For the python script you need these 7 files:
- [GP Albumless tracker.py](https://github.com/abppbd/Google-Photos-Albumless-Tracker/blob/main/GP%20Albumless%20tracker.py)
- [find_albumless_media.py](https://github.com/abppbd/Google-Photos-Albumless-Tracker/blob/main/find_albumless_media.py)
- [web_bot_controller.py](https://github.com/abppbd/Google-Photos-Albumless-Tracker/blob/main/web_bot_controller.py)
- [web_bot_functions.py](https://github.com/abppbd/Google-Photos-Albumless-Tracker/blob/main/web_bot_functions.py)
- [workers.py](https://github.com/abppbd/Google-Photos-Albumless-Tracker/blob/main/workers.py)
- [GPAT light mode v2.ico](https://github.com/abppbd/Google-Photos-Albumless-Tracker/blob/main/GPAT%20light%20mode%20v2.ico) (optional)
- [GPAT dark mode v2.ico](https://github.com/abppbd/Google-Photos-Albumless-Tracker/blob/main/GPAT%20dark%20mode%20v2.ico) (optional)

## Running
The main script is [GP Albumless tracker.py](https://github.com/abppbd/Google-Photos-Albumless-Tracker/blob/main/GP%20Albumless%20tracker.py), launch it to start the app.
A window should appear, more [info here](#usage).


# From the EXE build
## Requirements
Python and all the needed packages are bundled with the .exe file.

### rClone
The executable file uses [rClone](https://rclone.org/) which should be downloaded.
- (Recommended) For the satandalone executable, go to [rClone downloads](https://rclone.org/downloads), download the appropriate one for your device, and place it in the folder "GP Albumless tracker", next to the executable. <sub>(tested with _GPAT_)</sub>
- To install it on your machine, go to [rClone install](https://rclone.org/install) and follow the instructions. <sub>(/!\ not tested with _GPAT_ /!\\)</sub>
You will have to create a "remote" to your Google Photos account, [follow the instructions with "rclone config"](https://rclone.org/googlephotos/#configuration).

## Running
From file explorer or from the command line, navigate to where GPTA's and rclone's executables are located, then launch "GP Albumless tracker.exe".
A window should appear, more [info here](#usage).


# Usage
When the app launches there will be three tabs in the window, if some a greyed out it means you can not perform certain actions.

## Tab 1: Select your remote
Here you choose the remote you wish to search.
> If you create a remote while the app is opened, hit `Refresh` to update the list of remotes.

## Tab 2: Search for Albumless
Here you can launch the search for the selected remote with the `Search for albumless media` button.
The search might take a while and all the tabs will be disabled to avoid spam.
> The longest operation is fetching all the items in every album.

## Tab 3: Listing & Add to Album
Here, after searching, the list if the media items' names and their respective links will be displayed side by side.
When clicking on the `Open the Web Bot Controller` button, you will open the web bot.

### GPAT Web Bot
When the web bot is launched a `Web Bot Controller` (WBC) window and a `chrome browser` window will open, they compose the web bot.

1) In the chrome browser you will be prompted to log in to your Google Photos account.
2) Navigate into the album where all albumless media items will be placed (you can create a new one), and press `Select the Album` in the WBC .
3) Press `Go` to start the adding the media items to the album. (On the WBC a list of "do & don't while the web bot runs" is displayed, follow it.)

While the web bot runs you can paus it with the same button (the web bot can take up to 10s to stop).
Use the `Kill` button to close the web bot.


# Info & Credits
- The GUI was made using [PyQt6](https://www.riverbankcomputing.com/software/pyqt).
- Calls to the Google Photos' API are handled by rClone through the [python-rclone](https://github.com/Johannes11833/rclone_python) library by Johannes11833.
- Due to the Google photos API heavy limitations >:( , a web bot, based on [Selenium WebDriver's](https://www.selenium.dev/) chromedriver, is used feign a user manually adding the media items to the album.
- The executable bundle was made with the [PyInstaller](https://pyinstaller.org/en/stable/) package.
- The Web Bot and the rest of the application was written by me ([abppbd](https://github.com/abppbd)).


# Possible Failure Points
- The executable file might be considered a virus by anti-virus software. It is a [know problem with PyInstaller](https://github.com/pyinstaller/pyinstaller/issues/6754).
- Google Photos might update their API, breaking the albumless search. a Fix might be upgrading rClone and rclone-python (From pytho scripts only).
- Google might change the log in conditions, blocking the chrome window from loging into Google Photos.
- Google Photos might change their web layout, confusing the web bot and disabling it.