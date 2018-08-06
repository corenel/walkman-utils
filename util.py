import os

from appscript import app


def get_itunes_playlists():
    """
    Get list of playlist from iTunes

    :return: playlists in iTunes
    :rtype: list
    """
    return app('iTunes').user_playlists()


def get_files_in_playlist(playlists):
    """
    Get file path of desired playlists in iTunes

    :param playlists: name of desired playlists
    :type playlists: str or list[str]
    :return: list of file path
    :rtype: list[str]
    """
    if isinstance(playlists, str):
        playlists = [playlists]
    files_in_playlist = []

    for playlist in get_itunes_playlists():
        if playlist.name() in playlists:
            for track in playlist.file_tracks():
                files_in_playlist.append(track.location().path)

    return files_in_playlist


def split_filepath(files):
    """
    get common prefix and relative filepath

    :param files: list of filepath
    :type files: list[str]
    :return: common prefix and relative filepath
    :rtype: tuple(sre, list[str])
    """
    common_prefix = os.path.commonprefix(files)
    relative_paths = [f.replace(common_prefix, '') for f in files]
    return common_prefix, relative_paths


def scan_directory(target):
    """
    Scan given directory and get file lists

    :param target: target directory
    :type target: str
    :return: relative file lists
    :rtype: list[str]
    """
    if not target.endswith('/'):
        target += '/'
    relative_path = []

    for root, dirs, files in os.walk(target):
        curr = root.replace(target, '')
        for f in files:
            relative_path.append(os.path.join(curr, f))

    return relative_path


def compare_filelists(files_src, files_dst, root_src, root_dst):
    """
    Compare two file lists

    :param files_src: list of files in source directory
    :type files_src: list[str]
    :param files_dst: list of files in source directory
    :type files_dst: list[str]
    :param root_src: path to source directory
    :type root_src: str
    :param root_dst: path to source directory
    :type root_dst: str
    :return: list of files to be updated, removed and ignored
    :rtype: tuple(list, list, list)
    """
    to_be_updated = [x for x in files_src if x not in files_dst]
    to_be_removed = [x for x in files_dst if x not in files_src]
    to_be_ignored = []

    files_on_both_sides = [x for x in files_src if x in files_dst]
    for f in files_on_both_sides:
        if os.path.getmtime(os.path.join(root_src, f)) > \
                os.path.getmtime(os.path.join(root_dst, f)):
            to_be_updated.append(f)
        else:
            to_be_ignored.append(f)

    return to_be_updated, to_be_removed, to_be_ignored


def is_extension(filepath, ext):
    """
    Check whether file extension is desired

    :param filepath: path to file
    :type filepath: str
    :param ext: valid extension
    :type ext: str or list
    :return: whether file extension is desired
    :rtype: bool
    """
    if isinstance(ext, str):
        ext = [ext]
    filename, fileext = os.path.splitext(filepath)
    return fileext in ext


def get_lyrics_filename(track):
    """
    Get lyrics filename of given track

    :param track: given track
    :return: lyrics filename
    :rtype: str
    """
    title = track.title().replace('/', '&')
    artist = track.artist().replace('/', '&')
    return "{}) - {}.lrcx".format(title, artist)
