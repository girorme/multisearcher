#!/usr/bin/env python3
# -*- encoding: utf8 -*-
# Multi searcher
#
# The MultiSearcher is an open source scan which uses some engines
# to find web sites with the use of keywords and phrases.
#
# Current engines:
# [ask, bing, rambler.ru]
#
# Made to be simple, so this is not bug free.
# Feel free to fork and send a pull request to contribute ;).

import aiofiles
import time
import sys
import argparse
import os
import re
import aiohttp
import asyncio  # corutines
from requests.utils import requote_uri
from bs4 import BeautifulSoup


class MultiSearcher:
    ENGINE_BING = 'bing'
    ENGINE_ASK = 'ask'
    ENGINE_RAMBLER = 'rambler'

    def __init__(self, dork_file, output, threads):
        self.dork_file = dork_file
        self.output = output
        self.links = []
        self.ptr_limits = {
            'bing': 411,
            'ask': 20,
            'rambler': 20
        }
        self.exclude_items = 'msn|microsoft|php-brasil|facebook|' \
                             '4shared|bing|imasters|phpbrasil|php.net|yahoo|' \
                             'scrwordtbrasil|under-linux|google|msdn|ask|' \
                             'bing|rambler|youtube'
        self.engines = {
            MultiSearcher.ENGINE_BING: {
                'progress_string': '[Bing] Querying page {}/{} with dork {}\n',
                'search_string': 'https://www.bing.com/search?q={}&count=50&first={}',
                'page_range': range(1, self.ptr_limits['bing'], 10)
            },
            # MultiSearcher.ENGINE_ASK: {
            #     'progress_string': '[Ask] Querying page {}/{} with dork {}\n',
            #     'search_string': 'http://www.ask.com/web?q={}&page={}',
            #     'page_range': range(1, self.ptr_limits['ask'])
            # },
            # MultiSearcher.ENGINE_RAMBLER: {
            #     'progress_string': '[Rambler] Querying page {}/{} with dork {}\n',
            #     'search_string': 'http://nova.rambler.ru/search?query={}&page={}',
            #     'page_range': range(1, self.ptr_limits['rambler'])
            # }
        }

        self.threads = threads
        self.terminal = sys.stdout

    def get_engines(self):
        """Get current engines"""
        return self.engines

    def is_valid_link(self, link):
        "Check if a link is valid or not"
        return (
            link is not None
            and "http" in link
            and not re.search(self.exclude_items, link)
            and link not in self.links
        )

    async def get_links(self, session, word, engine):
        """Fetch links from engines asynchronously"""

        if not os.path.exists('output'):  # check if the output folder exists
            print('Output folder does not exist, creating it...')
            os.makedirs('output')  # create the output folder

        current_engine = self.engines[engine]

        for ptr in current_engine['page_range']:
            self.terminal.write(current_engine['progress_string'].format(
                ptr, self.ptr_limits[engine], word
            ))
            self.terminal.flush()

            word_encoded = requote_uri(word)
            url = current_engine['search_string'].format(
                word_encoded, str(ptr))

            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        continue

                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')

                    for link in soup.find_all('a', {'class': 'tilk'}):
                        link = link.get('href')
                        if self.is_valid_link(link):
                            self.links.append(link)
                            async with aiofiles.open(f'output/{self.output}', 'a+') as fd:
                                await fd.write(link + '\n')

            except Exception as e:
                print(f'Error: {e}')

    async def search(self, word):
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.get_links(session, word, engine)
                for engine in self.get_engines()
            ]
            await asyncio.gather(*tasks)

    async def main(self, debug=False):
        if debug == True:
            start = time.time()

        tasks = []
        async with aiohttp.ClientSession():
            with open(self.dork_file, 'r') as f:
                for word in f:
                    word = word.strip()
                    tasks.append(self.search(word))

            await asyncio.gather(*tasks)

        if debug == True:
            end = time.time()
        print(f"Finished! Output saved in output/{self.output}")
        if debug == True:
            print(f"Elapsed time {round(end - start, 2)}s")


def parseArgs():
    parser = argparse.ArgumentParser(description='Procz Multi Searcher')

    parser.add_argument(
        '-f', '--file',
        action='store',
        dest='dork_file',
        help='List with dorks to scan (One per line)',
        required=True
    )
    parser.add_argument(
        '-o', '--output',
        action='store',
        dest='output',
        help='Output to save valid results',
        default='output.txt'
    )
    parser.add_argument(
        '-t', '--threads',
        action='store',
        default=1,
        dest='threads',
        help='Concurrent workers (By word)',
        type=int
    )
    parser.add_argument('--version', action='version',
                        version='%(prog)s 2.0.0')
    args = parser.parse_args()
    return args


def printBanner():
    banner = """
      __  __       _ _   _  _____                     _
     |  \/  |     | | | (_)/ ____|                   | |
     | \  / |_   _| | |_ _| (___   ___  __ _ _ __ ___| |__   ___ _ __
     | |\/| | | | | | __| |\___ \ / _ \/ _` | '__/ __| '_ \ / _ \ '__|
     | |  | | |_| | | |_| |____) |  __/ (_| | | | (__| | | |  __/ |
     |_|  |_|\__,_|_|\__|_|_____/ \___|\__,_|_|  \___|_| |_|\___|_|
    """
    print(banner)

# you can test the performances adding line_profiler library
# @profile   #enable this and run the command kernprof -l -v multisearcher.py to see how long various parts of the program executed


def run_test(debug=False):

    args = parseArgs()
    printBanner()

    if args.dork_file:
        if not os.path.isfile(args.dork_file):
            exit('File {} not found'.format(args.dork_file))

        multi_searcher = MultiSearcher(
            args.dork_file,
            args.output,
            args.threads
        )

        asyncio.run(multi_searcher.main(debug=debug))


if __name__ == "__main__":
    run_test(debug=True)
