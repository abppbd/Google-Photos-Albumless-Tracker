# Introduction
[Google Photos](https://photos.google.com/) allows you to create albums to
organize your media items (photos, videos...). But there is no easy way to see
which ones are in an album and which ones aren't.

_Albumless to album_ helps your find them and can add them to a "needs triage"
album for future sorting.

- [Instalation](instalation)
- [Running](running)
- [Usage](usage)
- [Info & Credits](#info--credits)
- [Possible Failure Points](possible-failure-points)

---

# Instalation
## rClone
Rclone is _needed_ and a single executable.

For just a standalone executable, go to
[rClone downloads](https://rclone.org/downloads/) and download the appropriate
one for your device.
> (tested with _Albuless to album_)

If you wish to install it on your machine, go to
[rClone install](https://rclone.org/install/)
> (/!\ not tested with _Albuless to album_ /!\\)

## Albuless to album
### Standalone .exe
not implemented yet.
### Python source code
Download the files "GP Albumless tracker.py", "find_albumless_media.py", and
"add_to_album_web_bot.py".

> /!\ If your rClone is a single executable: place three python files and the
> executable in the same folder. /!\
> 
> Otherwise ensures that the three python files are together.

---

# Running
### Standalone .exe
not implemented yet.
### Python source code
1. Make sure "GP Albumless tracker.py", "find_albumless_media.py",
   "add_to_album_web_bot.py" and rClone executable are in the same folder then
   run **"GP Albumless tracker.py"**
3. Run **"GP Albumless tracker.py"** with your python interpreter

---

# Usage
Before AtA can be used, you need to give rclone acces to your Google Photos by
creating a [GP remote](https://rclone.org/googlephotos/#configuration). (The
remote can be read only, it won't be used to add media items to the album.)

## 1) Select your remote
On the First tab you'll choose the remote you wish to search.
> If you create a remote while the app is opened, hit `Refresh` to update the
> list of remotes.

## 2) Search for Albumless
On the Second tab you can launch the albumless search for the selected remotes.
The search might take a while and all controls of the window will be disabled,
don't close the window ! A status label shows the progress.
> The longest operation is fetching al the items in an album.

## 3) Listing & Add to Album
On the Third tab, after searching, the list if the media items' names and links
will be displayed side by side.

---

# Info & Credits
- The GUI was made using PyQt6.
- Calls to the Google Photos' API are handled by rclone through the
  [python-rclone](https://github.com/Johannes11833/rclone_python) library by
  Johannes11833.
- Due to the Google photos API limitation, a web bot, based on
  [Selenium WebDriver](https://www.selenium.dev/) chromedriver, is used feign
  the user manually adding the media items to the album.

---

# Possible Failure Points
- Google Photos might update their API, breaking the albumless search.
- Google might change the login conditions, blocking the web bot.
- Google Photos might change their web layout, making the web bot useless.
