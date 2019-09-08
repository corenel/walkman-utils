import os
import re
import click
import shutil
import unicodedata

from appscript import app, k
from tqdm import tqdm


def confirm(text, fg='green', **kwargs):
    """
    Confirm prompt

    :param text: prompt text
    :type text: str
    :param fg: foreground color
    :type fg: str
    :param kwargs: other arguments
    :return: confirmation result
    """
    return click.confirm(click.style('> {}'.format(text), fg=fg, bold=True),
                         **kwargs)


def status(text):
    """
    Print running status

    :param text: status text
    :type text: str
    """
    click.secho('{}'.format(text), fg='blue', bold=True)


def info(text):
    """
    Print running info

    :param text: status text
    :type text: str
    """
    click.secho('{}'.format(text), fg='green', bold=True)


def warning(text):
    """
    Print warning message

    :param text: warning message
    :type text: str
    """
    click.secho('{}'.format(text), fg='yellow', bold=True)


def error(text):
    """
    Print error message

    :param text: error message
    :type text: str
    """
    click.secho('{}'.format(text), fg='red', bold=True)
    # sys.exit(1)


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


def valid_value(value):
    return value != k.missing_value


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
    files_in_playlist = [
        t.location().path for t in tracks_in_playlist
        if valid_value(t.location())
    ]
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
    files_in_playlist = [
        get_lyrics_path(t.location().path) for t in tracks_in_playlist
        if valid_value(t.location())
    ]
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
                os.path.getmtime(os.path.join(root_dst, compose_str(f))):
            print(f)
            print(os.path.getmtime(os.path.join(root_src, f)))
            print(os.path.getmtime(os.path.join(root_dst, compose_str(f))))
            to_be_updated.append(f)
        else:
            to_be_ignored.append(f)

    return to_be_updated, to_be_removed, to_be_ignored


def sync_filelists(to_be_updated,
                   to_be_removed,
                   src_dir,
                   dst_dir,
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
            if os.path.exists(os.path.join(src_dir, file)):
                progress.set_description('Updating {}'.format(
                    os.path.basename(file)))
                target_file = os.path.join(dst_dir, compose_str(file))
                target_dir = os.path.dirname(target_file)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                shutil.copy2(os.path.join(src_dir, file),
                             os.path.join(dst_dir, compose_str(file)))
    else:
        print('Nothing to update')

    if len(to_be_removed) > 0 and remove_unmatched:
        progress = tqdm(sorted(to_be_removed))
        for file in progress:
            if os.path.exists(os.path.join(src_dir, file)):
                progress.set_description('Removing {}'.format(
                    os.path.basename(file)))
                target_file = os.path.join(dst_dir, compose_str(file))
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
    """
    Convert song file path to corresponding lyrics file path

    :param song: path to song file
    :type song: str
    :return: path to corresponding lyrics file
    :rtype: str
    """
    return os.path.splitext(song)[0] + '.lrc'


def format_timestamp(timestamp):
    """
    Format timestamp xx:xx.xxx as xx:xx.xx

    :param timestamp: timestamp
    :type timestamp: str
    :return: formatted timestamp
    :rtype: str
    """
    if len(re.findall('\d+:\d+\.\d\d\d', timestamp)) != 0:
        timestamp = re.findall('\d+:\d+\.\d\d\d', timestamp)[0]
        tsp = timestamp.split(':')
        return '%s:%05.2f' % (tsp[0], float(tsp[1]))
    elif len(re.findall('\d+:\d+\.\d\d', timestamp)) == 0:
        # print(timestamp)
        pass
    return timestamp


def format_lyrics(lrc_file):
    """
    Parse lyrics file and convert it to walkman-compatible format

    :param lrc_file: path to lyrics file
    :type lrc_file: str
    :return: lyrics in walkman-compatible format
    :rtype: str
    """
    formatted = []
    with open(lrc_file) as f:
        lines = f.readlines()
        lrc_lines = [
            l.strip() for l in lines
            if re.findall('\[\d+:\d+\.\d+\]', l) != [] and '[tr]' not in l
            and '[tt]' not in l
        ]
        for idx, lrc_line in enumerate(lrc_lines):
            if idx + 1 == len(lrc_lines):
                continue
            curr_timestamp = re.findall('\d+:\d+\.\d+', lrc_line)[0]
            next_timestamp = re.findall('\d+:\d+\.\d+', lrc_lines[idx + 1])[0]
            curr_timestamp_formatted = format_timestamp(curr_timestamp)
            next_timestamp_formatted = format_timestamp(next_timestamp)

            curr_line_split = lrc_line.split('[{}]'.format(curr_timestamp))
            curr_lyrics = curr_line_split[1] if len(
                curr_line_split) == 2 else ''

            formatted.append('[{}][{}]{}'.format(curr_timestamp_formatted,
                                                 next_timestamp_formatted,
                                                 curr_lyrics))

    with open(lrc_file, 'w') as f:
        f.write('\n'.join(formatted))


def struct_lyrics_dir(tracks, src_dir, dst_dir):
    """
    Copy lyrics file to given directory with the same structure as tracks

    :param tracks: list of tracks
    :type tracks: list
    :param src_dir: path to soruce directory
    :type src_dir: str
    :param dst_dir: path to target directory
    :type dst_dir: str
    """
    # get files
    files = [t.location().path for t in tracks if valid_value(t.location())]
    common_prefix = os.path.commonprefix(files)
    relative_paths = [
        get_lyrics_path(f.replace(common_prefix, '')) for f in files
    ]

    progress = tqdm(tracks)
    for idx, track in enumerate(progress):
        lrc_src = get_lyricsx_file(track, src_dir)
        if lrc_src is not None:
            lrc_dst = os.path.join(dst_dir, relative_paths[idx])
            if not os.path.exists(os.path.dirname(lrc_dst)):
                os.makedirs(os.path.dirname(lrc_dst))
            progress.set_description('Copying {}'.format(
                os.path.basename(lrc_dst)))
            shutil.copy2(lrc_src, lrc_dst)
            format_lyrics(lrc_dst)


def format_playlist_with_prefix(songs, prefix):
    """
    Format track list in relative paths with given prefix

    :param songs: list of songs
    :type songs: list[str]
    :param prefix: path prefix
    :type prefix: str
    :return: track list in relative paths with given prefix
    :rtype: list[str]
    """
    _, songs_rel = split_filepath(songs)
    songs_with_prefix = [
        os.path.join(prefix, compose_str(song)).replace('/', '\\')
        for song in songs_rel
    ]
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


def ord_to_str(ord_list):
    """
    Convert list of character orders to string

    :param ord_list: list of character orders
    :type ord_list: int or list[int]
    :return: corresponding string
    :rtype: str
    """
    if isinstance(ord_list, int):
        ord_list = [ord_list]
    s = ''
    for o in ord_list:
        s += chr(o)
    return s


def locate_all_occurrence(l, e):
    """
    Return indices of all element occurrences in given list

    :param l: given list
    :type l: list
    :param e: element to locate
    :return: indices of all occurrences
    :rtype: list
    """
    return [i for i, x in enumerate(l) if x == e]


def compose_str(s):
    """
    Replace decomposed character (like 0x3099 or 0x309a) in given string
    with composed one

    :param s: given string
    :type s: str
    :return: composed string
    :rtype: str
    """
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


def decompose_str(s):
    """
    Replace composed character in given string with decomposed one
    (like 0x3099 or 0x309a)

    :param s: given string
    :type s: str
    :return: decomposed string
    :rtype: str
    """
    return unicodedata.normalize('NFD', s)
