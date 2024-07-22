#Albumless to Album

##Finding albumless media items:
    This python program uses the python-rclone library to interact with the rClone executable to make requests to the Google Photos API.

##Adding Albumless media to an album:
    Because if Google Photos API limitations (😠) selenium us used to create a web bot to feign the user manually adding the media items to the album.

##Possible Failure Points:
    - Google Photos might update their API, breaking the albumless search.
    - Google might change the login conditions, blocking the web bot.
    - Tge Google Photos might change their layout, making the web bot useless.