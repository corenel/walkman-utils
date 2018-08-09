import os
import shutil
import unicodedata

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

    Note that path to track file may contain decomposed japanese
    character like `0x3099` and `0x309a`, which won"t recognized by walkman

    :param playlists: name of desired playlists
    :type playlists: str or list[str]
    :return: list of file path
    :rtype: list[str]
    """
    tracks_in_playlist = get_tracks_in_playlist(playlists)
    files_in_playlist = [t.location().path for t in tracks_in_playlist]
    return files_in_playlist


def get_lyrics_files_in_playlist(playlists):
    """
    Get lyrics file path of desired playlists in iTunes

    Note that path to lyrics file may contain decomposed japanese
    character like `0x3099` and `0x309a`, which won"t recognized by walkman

    :param playlists: name of desired playlists
    :type playlists: str or list[str]
    :return: list of lyrics file path
    :rtype: list[str]
    """
    tracks_in_playlist = get_tracks_in_playlist(playlists)
    files_in_playlist = [get_lyrics_path(t.location().path) for t in tracks_in_playlist]
    return files_in_playlist


def split_filepath(files):
    """
    get common prefix and relative filepath

    :param files: list of filepath
    :type files: list[str]
    :return: common prefix and relative filepath
    :rtype: tuple(str, list[str])
    """
    common_prefix = os.path.commonprefix(files)
    relative_paths = [f.replace(common_prefix, '') for f in files]
    return common_prefix, relative_paths


def scan_directory(target, extension):
    """
    Scan given directory and get file lists

    Note that `os.walk()` will return a path with decomposed japanese
    character like `0x3099` and `0x309a` despite the real path is composed

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

    Note that `files_src`, `files_dst` and files in `root_src` may contain
    decomposed japanese character like `0x3099` and `0x309a`.
    While files in `root_dst` won't.

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
    eps = 0.01
    for f in files_on_both_sides:
        if os.path.getmtime(os.path.join(root_src, f)) - eps > \
                os.path.getmtime(os.path.join(root_dst, correct_japanese_voice(f))):
            print(f)
            print(os.path.getmtime(os.path.join(root_src, f)))
            print(os.path.getmtime(os.path.join(root_dst, correct_japanese_voice(f))))
            to_be_updated.append(f)
        else:
            to_be_ignored.append(f)

    return to_be_updated, to_be_removed, to_be_ignored


def sync_filelists(to_be_updated, to_be_removed,
                   src_dir, dst_dir,
                   remove_unmatched=False):
    """
    Sync list of files from source directory to target

    :param to_be_updated: files to update
    :type to_be_updated: list[str]
    :param to_be_removed: files to remove
    :type to_be_removed: list[str]
    :param src_dir: path to source directory
    :type src_dir: str
    :param dst_dir: path to target directory
    :type dst_dir: str
    :param remove_unmatched: whether to remove unmatched files or not
    :type remove_unmatched: bool
    """
    if len(to_be_updated) > 0:
        progress = tqdm(sorted(to_be_updated))
        for file in progress:
            progress.set_description('Updating {}'.format(os.path.basename(file)))
            target_file = os.path.join(dst_dir, correct_japanese_voice(file))
            target_dir = os.path.dirname(target_file)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            shutil.copy2(os.path.join(src_dir, file),
                         os.path.join(dst_dir, correct_japanese_voice(file)))
    else:
        print('Nothing to update')

    if len(to_be_removed) > 0 and remove_unmatched:
        progress = tqdm(sorted(to_be_removed))
        for file in progress:
            progress.set_description('Removing {}'.format(os.path.basename(file)))
            target_file = os.path.join(dst_dir, correct_japanese_voice(file))
            os.remove(target_file)
    else:
        print('Nothing to remove')


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


def get_lyricsx_file(track, lyrics_dir):
    """
    Get lyrics file of given track in LyricsX directory

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


def get_lyrics_path(song):
    return os.path.splitext(song)[0] + '.lrc'


def parse_lyrics(filepath):
    """
    Parse lyrics file and convert it to walkman-compatible format

    :param filepath: path to lyrics file
    :type filepath: str
    :return: lyrics in walkman-compatible format
    :rtype: str
    """
    raise NotImplementedError


def struct_lyrics_dir(tracks, src_dir, dst_dir):
    # get files
    files = [t.location().path for t in tracks]
    common_prefix = os.path.commonprefix(files)
    relative_paths = [get_lyrics_path(f.replace(common_prefix, ''))
                      for f in files]

    progress = tqdm(tracks)
    for idx, track in enumerate(progress):
        lrc_src = get_lyricsx_file(track, src_dir)
        if lrc_src is not None:
            lrc_dst = os.path.join(dst_dir, relative_paths[idx])
            if not os.path.exists(os.path.dirname(lrc_dst)):
                os.makedirs(os.path.dirname(lrc_dst))
            progress.set_description('Copying {}'.format(os.path.basename(lrc_dst)))
            shutil.copy2(lrc_src, lrc_dst)


def generate_playlist_with_prefix(songs, prefix):
    _, songs_rel = split_filepath(songs)
    songs_with_prefix = [os.path.join(prefix, correct_japanese_voice(song)).replace('/', '\\')
                         for song in songs_rel]
    return songs_with_prefix


def str_to_ord(s):
    """
    Convert string to list of character orders

    :param s: given string
    :type s: str
    :return: list of character orders
    :rtype: list[int]
    """
    return [ord(c) for c in s]


#
#
# def ord_to_str(ord_list):
#     """
#     Convert list of character orders to string
#
#     :param ord_list: list of character orders
#     :type ord_list: int or list[int]
#     :return: corresponding string
#     :rtype: str
#     """
#     if isinstance(ord_list, int):
#         ord_list = [ord_list]
#     s = ''
#     for o in ord_list:
#         s += chr(o)
#     return s
#
#
# def locate_all_occurrence(l, e):
#     """
#     Return indices of all element occurrences in given list
#
#     :param l: given list
#     :type l: list
#     :param e: element to locate
#     :return: indices of all occurrences
#     :rtype: list
#     """
#     return [i for i, x in enumerate(l) if x == e]


def correct_japanese_voice(s):
    # char_list = str_to_ord(s)
    # corrected_list = []
    # voice_mark = locate_all_occurrence(char_list, 0x3099)
    # semivoice_mark = locate_all_occurrence(char_list, 0x309a)
    #
    # curr_idx = 0
    # while curr_idx < len(char_list):
    #     if curr_idx + 1 in voice_mark:
    #         corrected_ord = char_list[curr_idx] + 1
    #         corrected_list.append(corrected_ord)
    #         curr_idx += 2
    #     elif curr_idx + 1 in semivoice_mark:
    #         corrected_ord = char_list[curr_idx] + 2
    #         corrected_list.append(corrected_ord)
    #         curr_idx += 2
    #     else:
    #         corrected_list.append(char_list[curr_idx])
    #         curr_idx += 1
    #
    # return ord_to_str(corrected_list)
    return unicodedata.normalize('NFC', s)


def restore_japanese_voice(s):
    return unicodedata.normalize('NFD', s)
