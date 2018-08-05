import util


def sync_playlist(playlists, target_dir):
    files_in_playlists = util.get_files_in_playlist(playlists)
    itunes_folder, files_in_itunes = util.split_filepath(files_in_playlists)
    files_on_walkman = util.scan_directory(target_dir)


if __name__ == '__main__':
    print(util.scan_directory('.'))
