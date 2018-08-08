import os
import shutil

from appscript import app
from tqdm import tqdm


def get_itunes_playlists():
    """
    Get list of playlist from iTunes

    :return: playlists in iTunes
    :rtype: list
    """
    return app('iTunes').user_playlists()


def get_tracks_in_playlist(playlists):
    """
    Get tracks of desired playlists in iTunes

    :param playlists: name of desired playlists
    :type playlists: str or list[str]
    :return: list of file path
    :rtype: list
    """
    if isinstance(playlists, str):
        playlists = [playlists]
    tracks_in_playlist = []

    for playlist in get_itunes_playlists():
        if playlist.name() in playlists:
            for track in playlist.file_tracks():
                tracks_in_playlist.append(track)

    return tracks_in_playlist


def get_files_in_playlist(playlists):
    """
    Get file path of desired playlists in iTunes

    :param playlists: name of desired playlists
    :type playlists: str or list[str]
    :return: list of file path
    :rtype: list[str]
    """
    tracks_in_playlist = get_tracks_in_playlist(playlists)
    files_in_playlist = [t.location().path for t in tracks_in_playlist]
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


def scan_directory(target, extension):
    """
    Scan given directory and get file lists

    :param target: target directory
    :type target: str
    :param extension: valid extension
    :type extension: str or list[str]
    :return: relative file lists
    :rtype: list[str]
    """
    if not target.endswith('/'):
        target += '/'
    relative_path = []

    for root, dirs, files in os.walk(target):
        curr = root.replace(target, '')
        for f in files:
            if is_extension(f, extension):
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


def sync_filelists(to_be_updated, to_be_removed,
                   src_dir, dst_dir,
                   remove_unmatched=False):
    progress = tqdm(sorted(to_be_updated))
    for music in progress:
        progress.set_description('Updating {}'.format(os.path.basename(music)))
        target_path = os.path.join(dst_dir, os.path.dirname(music))
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        shutil.copy2(os.path.join(src_dir, music), target_path)

    if remove_unmatched:
        progress = tqdm(sorted(to_be_removed))
        for music in progress:
            progress.set_description('Removing {}'.format(os.path.basename(music)))
            target_path = os.path.join(dst_dir, os.path.dirname(music))
            os.remove(target_path)


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
    filename, file_ext = os.path.splitext(filepath)
    return file_ext in ext


def get_lyrics_file(track, lyrics_dir):
    """
    Get lyrics file of given track

    :param track: given track
    :param lyrics_dir: root directory of lyrics files
    :type lyrics_dir: str
    :return: lyrics filename
    :rtype: str
    """
    title = track.name().replace('/', '&')
    artist = track.artist().replace('/', '&')
    lrc_file = os.path.join(lyrics_dir, "{} - {}.lrcx".format(title, artist))
    if os.path.exists(lrc_file):
        return lrc_file
    else:
        return None


def parse_lyrics(filepath):
    """
    Parse lyrics file and convert it to walkman-compatible format

    :param filepath: path to lyrics file
    :type filepath: str
    :return: lyrics in walkman-compatible format
    :rtype: str
    """
    raise NotImplementedError
