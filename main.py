import os
import util
import setting

from tqdm import tqdm


def sync_playlist(playlists, walkman_dir, remove_unmatched=False):
    # Get music list
    songs_in_playlists = util.get_files_in_playlist(playlists)
    itunes_folder, songs_in_playlists_rel = util.split_filepath(songs_in_playlists)
    music_on_walkman = util.scan_directory(walkman_dir, setting.MUSIC_FILE_EXT)
    to_be_updated, to_be_removed, _ = util.compare_filelists(
        songs_in_playlists_rel, music_on_walkman,
        root_src=itunes_folder, root_dst=walkman_dir
    )

    # Update music
    util.sync_filelists(to_be_updated, to_be_removed,
                        src_dir=itunes_folder, dst_dir=walkman_dir,
                        remove_unmatched=remove_unmatched)


def create_m3u_playlist(playlists, walkman_dir, walkman_prefix):
    progress = tqdm(playlists)
    for playlist in progress:
        progress.set_description('{}'.format(os.path.basename(playlist)))
        songs_in_playlists = util.get_files_in_playlist(playlist)
        songs_with_prefix = util.generate_playlist_with_prefix(songs_in_playlists,
                                                               walkman_prefix)
        with open(os.path.join(walkman_dir, '{}.m3u'.format(playlist)), 'w') as f:
            f.write('\n'.join(songs_with_prefix))
            f.write('\n')


def create_local_lyrics(playlists, lyrics_dir, lyrics_source_dir):
    tracks_in_playlist = util.get_tracks_in_playlist(playlists)
    util.struct_lyrics_dir(tracks_in_playlist,
                           src_dir=lyrics_source_dir,
                           dst_dir=lyrics_dir)


def sync_lyrics(playlists, lyrics_dir, walkman_dir, remove_unmatched=False):
    # Get lyrics list
    lyrics_on_local = util.get_lyrics_files_in_playlist(playlists)
    _, lyrics_on_local_rel = util.split_filepath(lyrics_on_local)
    lyrics_on_walkman = util.scan_directory(walkman_dir, setting.LYRICS_FILE_EXT)

    # Update lyrics
    to_be_updated, to_be_removed, _ = util.compare_filelists(
        lyrics_on_local_rel, lyrics_on_walkman,
        root_src=lyrics_dir, root_dst=walkman_dir
    )
    util.sync_filelists(to_be_updated, to_be_removed,
                        src_dir=lyrics_dir, dst_dir=walkman_dir,
                        remove_unmatched=remove_unmatched)


if __name__ == '__main__':
    sync_playlist(playlists=setting.PLAYLISTS,
                  walkman_dir=setting.WALKMAN_DIR)

    create_m3u_playlist(playlists=setting.PLAYLISTS,
                        walkman_dir=setting.WALKMAN_DIR,
                        walkman_prefix=setting.WALKMAN_PLAYLIST_PREFIX)

    create_local_lyrics(playlists=setting.PLAYLISTS,
                        lyrics_dir=setting.LYRICS_DIR,
                        lyrics_source_dir=setting.LYRICS_SOURCE_DIR)

    sync_lyrics(playlists=setting.PLAYLISTS,
                lyrics_dir=setting.LYRICS_DIR,
                walkman_dir=setting.WALKMAN_DIR)
