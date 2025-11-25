#!/usr/bin/env python3

'''
Send an http request to a url and format the response in an easy-to-parse format
'''

import prettytable
import re
import requests
import sys
import webbrowser

from bs4 import BeautifulSoup
from datetime import datetime

url_base = 'https://thepiratebay.org/search.php?q='


def format_bytes(size:int) -> str:
    '''Given an integer number of bytes, return the human-readable version of that'''
    power = 1024
    labels = {
        0: 'B',
        1: 'KB',
        2: 'MB',
        3: 'GB',
        4: 'TB',
    }
    n = 0
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + ' ' + labels[n]


def build_table_row(index:int, obj):
    '''Build the table to print to stdout for the user'''
    categories = {
        '0': '',
        '1': 'Audio',
        '2': 'Video',
        '3': 'Application',
        '4': 'Game',
        '5': 'Porn',
        '6': 'Other',
    }

    row = []
    row.append(i+1)
    row.append(categories[obj['category'][0]])
    row.append(obj['name'])
    row.append(format_bytes(int(obj['size'])))
    row.append(datetime.fromtimestamp(int(obj['added'])).strftime('%Y-%m-%d'))
    row.append(obj['username'])
    row.append(obj['seeders'])
    row.append(obj['leechers'])

    return row


def main():
    content_query = input('What would you like to download? ')
    response = requests.get(f'{url_base}{content_query}')
    
    soup = BeautifulSoup(response.content, 'html.parser')

    search_results = soup.select('div#main-content')

    if search_results:
        magnet_links = dict()

        headers = [
            'S.No',
            'Type',
            'Name',
            'Upload date',
            'Size',
            'Uploaded by',
            'Seeders',
            'Leechers',
        ]
        table = prettytable.PrettyTable(headers)
        table.align = 'l'
        table.padding_width = 2

        for i, result in enumerate(search_results):
            row = build_table_row(result)
            table.add_row(i+1, row)
            magnet = result.select_one('a[href^=magnet]')
            if magnet:
                magnet_links[i+1] = magnet

        # now that we've parsed the search results, print the table and ask for which element to download
        print(table)
        download_selection = input('Select which number to download')
        webbrowser.open(magnet_links[download_selection])

    else:
        print('Could not find any elements that matched your query')
        sys.exit(1)


if __name__ == '__main__':
    main()
