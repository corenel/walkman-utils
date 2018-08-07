import os
import util
import setting
import shutil

from tqdm import tqdm


def sync_playlist(playlists, walkman_dir, remove_unmatched=False):
    # Get music list
    music_in_playlists = util.get_files_in_playlist(playlists)
    itunes_folder, files_in_itunes = util.split_filepath(music_in_playlists)
    music_on_walkman = util.scan_directory(walkman_dir, setting.MUSIC_FILE_EXT)
    to_be_updated, to_be_removed, to_be_ignored = util.compare_filelists(
        music_in_playlists, music_on_walkman,
        root_src=itunes_folder, root_dst=walkman_dir
    )

    # Update music
    progress = tqdm(sorted(to_be_updated))
    for music in progress:
        progress.set_description('Updating {}'.format(os.path.basename(music)))
        target_path = os.path.join(walkman_dir, os.path.dirname(music))
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        shutil.copy2(os.path.join(itunes_folder, music), target_path)

    if remove_unmatched:
        progress = tqdm(sorted(to_be_removed))
        for music in progress:
            progress.set_description('Removing {}'.format(os.path.basename(music)))
            target_path = os.path.join(walkman_dir, os.path.dirname(music))
            os.remove(target_path)


def sync_lyrics(playlists, lyrics_dir, walkman_dir):
    tracks_in_playlist = util.get_tracks_in_playlist(playlists)
    lyrics_on_local = [util.get_lyrics_file(track, lyrics_dir)
                       for track in tracks_in_playlist]
    lyrics_on_local = [lrc for lrc in lyrics_on_local if lrc is not None]
    _, lyrics_on_local_rel = util.split_filepath(lyrics_on_local)
    lyrics_on_walkman = util.scan_directory(walkman_dir, setting.LYRICS_FILE_EXT)

    to_be_updated, to_be_removed, to_be_ignored = util.compare_filelists(
        lyrics_on_local_rel, lyrics_on_walkman,
        root_src=lyrics_dir, root_dst=walkman_dir
    )


if __name__ == '__main__':
    print(util.scan_directory('.'))
