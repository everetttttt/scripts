#!/usr/bin/env python3

'''
media player launcher

searches within a start directory for a search string
outputs all matches and opens your selection in Celluloid, my preferred media player
'''

import os
import subprocess
import sys

from string import punctuation, whitespace


start_dir = os.path.expanduser('~/Torrents')


def clean_string(s:str) -> str:
    '''remove punctuation and whitespace from a string'''
    return ''.join(c for c in s if c not in punctuation and c not in whitespace).lower()


def list_dirs(startdir:str) -> list[str]:
    '''returns a list of all subdirs from the start dirpath'''
    result = []
    if not os.path.isdir(startdir):
        raise FileNotFoundError(f'Start path {startdir} is not a valid directory')
    
    for root, _, _ in os.walk(startdir):
        result.append(os.path.relpath(root, startdir))

    return result


def can_be_found_subsequently(query:str, text:str) -> bool:
    '''check if query chars appear in order in text'''
    q_i = 0 # query index
    t_i = 0 # text index
    while q_i < len(query) and t_i < len(text):
        if query[q_i] == text[t_i]:
            q_i += 1
        t_i += 1
    return q_i == len(query)


def find_matches(query:str, dirs:list[str]) -> list[str]:
    '''find dirs that contain query's first word and then remaining chars in order'''
    # split query into first word and rest
    words = query.split()
    if not words:
        return []
    first_word = clean_string(words[0])
    remaining = clean_string(''.join(words[1:]))

    first_matches = [d for d in dirs if first_word in d.lower()]

    if remaining:
        return [d for d in first_matches if can_be_found_subsequently(remaining, d.lower())]
    return first_matches


def prompt_and_select(matches: list[str]) -> str:
    '''print matches with index and prompt user to choose one to open in Celluloid'''
    if not matches:
        print('No matches found!')
        sys.exit(1)
    
    matches = sorted(matches)

    for i, d in enumerate(matches, start=1):
        # print with ANSI escape codes for bold index text
        print(f'\033[1m{i}\033[0m.  {d}')

    prompt = input('Select folder to open or press another key to cancel: ')
    if prompt.isdigit() and 0 < int(prompt) <= len(matches):
        selection = matches[int(prompt) - 1]
        return selection
    else:
        print(f'Invalid selection {prompt}. Exiting...')
        sys.exit(1)


def open_in_celluloid(path:str) -> None:
    '''Open the given path in celluloid'''
    full_path = os.path.join(start_dir, path)
    try:
        subprocess.Popen(['celluloid', full_path], start_new_session=True)
    except subprocess.CalledProcessError:
        print(f'Error launching Celluloid')
        sys.exit(1)


def main() -> None:
    if len(sys.argv) == 1:
        query = input("Enter the tv show or movie you'd like to play: ")
    else:
        query = ' '.join(sys.argv[1:])

    dirs = list_dirs(start_dir)
    matches = find_matches(query, dirs)
    selection = prompt_and_select(matches)
    print(f'Opening {selection} in Celluloid...')
    open_in_celluloid(selection)

        

if __name__ == '__main__':
    main()
