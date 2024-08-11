"""
This script searches google photo for photos that are not in any album and
dumps them in a "needs triage" album.

Inspired by:
https://support.google.com/photos/thread/12363001?hl=en&msgid=81969237
"""

from rclone_python import rclone

#-----------------------------------------------------------------------------#
def ls_only_id(ls_json):
    # Remove unnecessary data returned by rclone.ls(), only keep IDs.
    ls_file_names = [item["ID"] for item in ls_json]
    return ls_file_names

#-----------------------------------------------------------------------------#
def id_to_name_dict(ls_json):
    # Make a dist associating the ID to the Name.
    id_to_name = {item["ID"]:item["Name"] for item in ls_json}
    return id_to_name

#-----------------------------------------------------------------------------#
def get_media_all(remote):
    # Fetching all media items in remote.

    ls_media_all = rclone.ls(remote + "media/all")
    # Fetching.
    ls_media_all_id = ls_only_id(ls_media_all)
    # Listing only IDs.
    ls_media_all_id_to_name = id_to_name_dict(ls_media_all)
    # Associate an ID to the file name.

    return ls_media_all_id, ls_media_all_id_to_name

#-----------------------------------------------------------------------------#
def get_album_media(remote):

    ls_album = rclone.ls(remote + "album")
    ls_album = [item["Name"] for item in ls_album]
    # Get list of albums' name.

    ls_album_media_files = []
    for album_name in ls_album:
        ls_album_media = rclone.ls(f"{remote}album/{album_name}")
        # Fetching.
        ls_album_media = ls_only_id(ls_album_media)
        # Listing only IDs.
        ls_album_media_files += ls_album_media
        # Add to IDs in album.
    # Fetch every media in any album

    return ls_album_media_files

#-----------------------------------------------------------------------------#
def albumless_links(media_name, media_id):
    # Returns a list of tuples containing the name and the url for every
    # albumless media item.

    links = []

    for name, ID in zip(media_name, media_id):
        links.append((name, ID))
        # Add name & google photo ID.
    return links

#-----------------------------------------------------------------------------#
def get_albumless_media(remote):

    yield "Fetching & Listing all media items in remote..."
    ls_media_all_id, ls_media_all_id_to_name = get_media_all(remote)
    # Get a list of all the medias & associating dict.

    yield "Fetching & Listing all media items in every remote's albums..."
    ls_album_media_files = get_album_media(remote)
    # Get a list of all the medias in albums.

    yield "Calculating difference..."
    ls_media_all_id = set(ls_media_all_id)
    ls_album_media_files = set(ls_album_media_files)
    # Remove duplicates.

    media_not_in_album_id = ls_media_all_id.difference(ls_album_media_files)
    # Get difference between the two sets.

    media_not_in_album_name = [
        ls_media_all_id_to_name[_] for _ in media_not_in_album_id
    ]
    # List of media's names not in album.

    # >:( Google Photo API doesn't support moving photos to album by 3rd party
    # tools, such BULLSHIT. >:(
    yield "Getting URL(s)..."
    links = albumless_links(media_not_in_album_name, media_not_in_album_id)
    # At least I can get the url.

    yield "Done. :)"

    yield links
