#!/usr/bin/env python3

# will need to put api key in ~/.opensubtitlesapirc

import logging
import os
import re
import stat
import sys
import time

from opensubtitlescom import OpenSubtitles


# configure logging
os.makedirs('out', exist_ok=True)
logging.basicConfig(
    filename='out/subtitles.log',
    level=logging.INFO,
    format='%(message)s',
)

# file extensions we'll search for
VIDEO_EXTENSIONS = [
    '.mp4',
    '.mkv',
    '.avi',
    '.mov',
    '.wmv',
    '.flv',
    '.webm',
]
SRT_EXTENSION = '.srt'


def get_api_key() -> tuple[str, str, str]:
    '''
    Get username, password, and api key for opensubtitles.com from ~/.opensubtitlesapirc
    '''
    def api_key_help():
        print(f'The contents should look like')
        print(f'user=<username>')
        print(f'pass=<password>')
        print(f'key=<api key>')
        sys.exit(1)

    rc_path = os.path.expanduser('~/.opensubtitlesapirc')
    if not os.path.exists(rc_path):
        print(f'{rc_path} does not exist! It must contain the user, pass, and key')
        api_key_help()

    # check file permissions
    st = os.stat(rc_path)
    if st.st_mode & 0o777 != 0o600:
        print(f'Error: {rc_path} must have 600 permissions (owner read/write only). Try `chmod 600 {rc_path}`')
        api_key_help()
    user = None
    passwd = None
    apikey = None
    try:
        with open(rc_path, 'r') as f:
            for line in f:
                if line.startswith('user='):
                    user = line.split('=', 1)[1].strip()
                elif line.startswith('pass='):
                    passwd = line.split('=', 1)[1].strip()
                elif line.startswith('key='):
                    apikey = line.split('=', 1)[1].strip()

        if user is None or passwd is None or apikey is None:
            print(f'Could not find all user, pass, and key in {rc_path}')
            api_key_help()
        return user, passwd, apikey
    except Exception as e:
        print(f'Could not read API key from {rc_path}: {e}')
        sys.exit(1)


def is_video_file(filename:str) -> bool:
    return any(filename.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)


def get_srt_filepath(filepath:str) -> str:
    return os.path.splitext(filepath)[0] + SRT_EXTENSION


def extract_show_info(filepath:str) -> tuple[str, int, int]:
    '''try to get show name, season, and episode from a filepath'''
    basename = os.path.basename(filepath)
    dirname = os.path.dirname(filepath)

    match = re.search(r'(S?(\d{1,2}))[ ._-]*E(\d{1,2})', basename, re.IGNORECASE)
    if not match:
        match = re.search(r'(S?(\d{1,2}))[ ._-]*E(\d{1,2})', dirname, re.IGNORECASE)

    if match:
        season = int(match.group(2))
        episode = int(match.group(3))
        show_name = os.path.basename(os.path.dirname(dirname))
        return show_name, season, episode
    return None, None, None


def extract_movie_info(filepath:str) -> str:
    '''use parent directory or filename as movie name'''
    dirname = os.path.dirname(filepath)
    if 'Movies' in dirname:
        movie_name = os.path.splitext(os.path.basename(filepath))[0]
        # remove common tags (year, resolution, etc)
        movie_name = re.sub(r'\b(19|20)\d{2}\b', '', movie_name)
        movie_name = re.sub(r'\b(720p|1080p|2160p|x264|x265|BluRay|WEBRip|HDRip|DVDRip)\b', '', movie_name, flags=re.IGNORECASE)
        movie_name = re.sub(r'[\.\-_]', ' ', movie_name)
        movie_name = movie_name.strip()
        return movie_name
    return None


def main() -> None:
    if len(sys.argv) < 2:
        print(f'Usage: {os.path.relpath(__file__)} <directory>')
        sys.exit(1)

    search_root = os.path.abspath(sys.argv[1])
    if not os.path.isdir(search_root):
        print(f'Error: {search_root} is not a directory')
        sys.exit(1)

    logging.info(f'\n\n==== Subtitle check started at {time.strftime('%Y-%m-%d %H:%M:%S')} ====')
    logging.info(f'Searching for subtitles in {search_root}')

    USER, PASS, API_KEY = get_api_key()
    client = OpenSubtitles(user_agent='SubtitleGrabber', api_key=API_KEY)
    client.login(username=USER, password=PASS)

    dir_status = {}

    # must go bottom up
    for dirpath, subdirs, filenames in os.walk(search_root, topdown=False):
        # skip if an ignore subtitle check file exists
        if '.ignoresubtitlecheck' in filenames:
            dir_status[dirpath] = (True, [])
            continue
        
        all_good = True
        table = []

        # check all video files in this dir
        for filename in filenames:
            if not is_video_file(filename):
                continue
            filepath = os.path.join(dirpath, filename)
            srt_path = get_srt_filepath(filepath)
            has_sub = os.path.exists(srt_path)
            if not has_sub:
                all_good = False

            table.append({
                'filepath': filepath,
                'has_sub': has_sub,
            })

        # check subdir status. this is why we must go bottom up
        for subdir in subdirs:
            subdir_path = os.path.join(dirpath, subdir)
            sub_good, _ = dir_status.get(subdir_path, (True, []))
            if not sub_good:
                all_good = False
        
        dir_status[dirpath] = (all_good, table)

    # now we go through the elements that we saved as not having subs
    # log them and attempt to retrieve subtitles
    for dirpath, (all_good, table) in dir_status.items():
        if all_good:
            logging.info(f'\n[{os.path.relpath(dirpath, search_root)}] looks good')
        else:
            logging.info(f'\n[{os.path.relpath(dirpath, search_root)}] status')
            logging.info(f'  {'Filename':40} | {'Extracted name':30} | {'Result'}')
            
            for element in table:
                filepath = element['filepath']
                has_sub = element['has_sub']
                if has_sub == True:
                    continue

                if 'Movies' in filepath:
                    movie_name = extract_movie_info(filepath)
                    log_string = movie_name
                    if not movie_name:
                        logging.info(f'  {os.path.relpath(filepath, dirpath):40} | {'':30} | Failed to extract movie name')
                        continue

                    try:
                        results = client.search(
                            query=movie_name, 
                            type='movie', 
                            languages='en'
                        )
                    except Exception as e:
                        logging.info(f'  {os.path.relpath(filepath, dirpath):40} | {log_string:30} | Failed API query: {e}')
                        continue

                else: # is a show
                    show_name, season, episode = extract_show_info(filepath)
                    if not show_name or not season or not episode:
                        logging.info(f'  {os.path.relpath(filepath, dirpath):40} | {'':30} | Failed to extract show name/season/episode')
                        continue
                    log_string = f'{show_name} S{season}E{episode}'

                    try:
                        results = client.search(
                            query=show_name,
                            season_number=season,
                            episode_number=episode,
                            type='episode',
                            languages='en',
                        )
                    except Exception as e:
                        logging.info(f'  {os.path.relpath(filepath, dirpath):40} | {log_string:30} | Failed API query: {e}')
                        continue
                    
                if not results or not results.data:
                    logging.info(f'  {os.path.relpath(filepath, dirpath):40} | {log_string:30} | No subtitles found!')
                    continue

                # download the first subtitle result
                try:
                    srt_path = get_srt_filepath(filepath)
                    client.download_and_save(results.data[0], filename=srt_path)
                    logging.info(f'  {os.path.relpath(filepath, dirpath):40} | {log_string:30} | Successfully downloaded')
                except Exception as e:
                    logging.info(f'  {os.path.relpath(filepath, dirpath):40} | {log_string:30} | Failed to download: {e}')
                    continue
                
                time.sleep(5) # be nice to the api

if __name__ == '__main__':
    main()
