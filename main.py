import os
import util
import shutil

from tqdm import tqdm


def sync_playlist(playlists, target_dir, remove_unmatched=False):
    # Get music list
    files_in_playlists = util.get_files_in_playlist(playlists)
    itunes_folder, files_in_itunes = util.split_filepath(files_in_playlists)
    files_on_walkman = util.scan_directory(target_dir)
    to_be_updated, to_be_removed, to_be_ignored = util.compare_filelists(
        files_in_playlists, files_on_walkman,
        root_src=itunes_folder, root_dst=target_dir
    )

    # Update music
    progress = tqdm(sorted(to_be_updated))
    for f in progress:
        progress.set_description('Updating {}'.format(os.path.basename(f)))
        target_path = os.path.join(target_dir, os.path.dirname(f))
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        shutil.copy2(os.path.join(itunes_folder, f), target_path)

    if remove_unmatched:
        progress = tqdm(sorted(to_be_removed))
        for f in progress:
            if not util.is_extension(f, 'lrc'):
                progress.set_description('Removing {}'.format(os.path.basename(f)))
                target_path = os.path.join(target_dir, os.path.dirname(f))
                os.remove(target_path)


if __name__ == '__main__':
    print(util.scan_directory('.'))
