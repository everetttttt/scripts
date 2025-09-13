#!/usr/bin/env python3

# pip install opensubtitlescom

# will need to put api key in ~/.opensubtitlesapirc

import logging
import os
import re
import sys
import time

from opensubtitlescom import OpenSubtitles

# configure logging
logging.basicConfig(
    filename='out/subtitles.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
)

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


def get_api_key() -> str:
    rc_path = os.path.expanduser('~/.opensubtitlesapirc')
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
            sys.exit(1)
        return user, passwd, apikey
    except Exception as e:
        print(f'Could not read API key from {rc_path}: {e}')
        sys.exit(1)

def get_is_video_file(filename:str) -> bool:
    return filename.lower().endswith(VIDEO_EXTENSIONS)

def get_srt_filepath(filepath:str) -> str:
    return os.path.splitext(filepath)[0] + SRT_EXTENSION

def extract_show_info(filepath:str) -> tuple[str, int, int]:
    '''try to get show name, season, and episode'''
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
    USER, PASS, API_KEY = get_api_key()
    client = OpenSubtitles(api_key=API_KEY)
    # client.login(username=USER, password=PASS)
    root_dir = os.getcwd()
    logging.info(f'Starting subtitle search in {root_dir}')

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if not get_is_video_file(filename):
                continue

            filepath = os.path.join(dirpath, filename)
            logging.info(filepath)

            srt_path = get_srt_filepath(filepath)
            if os.path.exists(srt_path):
                logging.info('    SUCCESS: subtitle already exists\n')
                continue

            if 'Movies' in dirpath:
                movie_name = extract_movie_info(filepath)
                if not movie_name:
                    logging.warning('    FAILED: could not extract movie name')
                    continue

                logging.info(f'    Searching subtitles for movie {movie_name}...')
                try:
                    results = client.search(
                        query=movie_name, 
                        type='movie', 
                        languages='en'
                    )
                except Exception as e:
                    logging.error(f'    FAILED: api query failed for {movie_name}:\n        {e}')
                    return

            else: # is a show
                show_name, season, episode = extract_show_info(filepath)
                if not show_name or not season or not episode:
                    logging.warning('    FAILED: could not extract show info')
                    continue

                logging.info(f'    Searching subtitles for show {show_name}, s{season} e{episode}')
                try:
                    results = client.search(
                        query=show_name,
                        season_number=season,
                        episode_number=episode,
                        type='episode',
                        languages='en',
                    )
                except Exception as e:
                    logging.error(f'    FAILED: api query failed for {show_name} s{season} e{episode}:\n        {e}')
                    return
                
            if not results or not results['data']:
                logging.warning(f'    No subtitles found!')
                continue

            # download the first subtitle result
            try:
                client.download_and_save(results.data[0], filename=srt_path)
                logging.info(f'    SUCCESS: downloaded subtitles')
            except Exception as e:
                logging.error(f'    FAILED: failed to download subtitles: {e}')
                return
            
            time.sleep(5) # be nice to the api

if __name__ == '__main__':
    main()
