#!/usr/bin/env python2.7
# -*- encoding: utf8 -*-
# Multi searcher
#
# The MultiSearcher is an open source scan which uses some engines
# to find web sites with the use of keywords and phrases.
#
# Current engines:
# [ask, bing, rambler.ru]
#
# Made to be simple, so this is not free of bugs.
# Feel free to fork and send a pull request to contribute ;).

import requests
import re
import os
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
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
        self.exclude_itens = 'msn|microsoft|php-brasil|facebook|' \
                             '4shared|bing|imasters|phpbrasil|php.net|yahoo|' \
                             'scrwordtbrasil|under-linux|google|msdn|ask|' \
                             'bing|rambler|youtube'
        self.engines = {
            MultiSearcher.ENGINE_BING: {
                'progress_string': '[Bing] Quering page {}/{} with dork {}',
                'search_string': 'http://www.bing.com/search?q={}&count=50&first={}',
                'page_range': range(1, self.ptr_limits['bing'], 10)
            },
            MultiSearcher.ENGINE_ASK: {
                'progress_string': '[Ask] Quering page {}/{} with dork {}',
                'search_string': 'http://www.ask.com/web?q={}&page={}',
                'page_range': range(1, self.ptr_limits['ask'])
            },
            MultiSearcher.ENGINE_RAMBLER: {
                'progress_string': '[Rambler] Quering page {}/{} with dork {}',
                'search_string': 'http://nova.rambler.ru/search?query={}&page={}',
                'page_range': range(1, self.ptr_limits['rambler'])
            }
        }

        self.threads = threads
        self.counter = 0
        self.list_size = len(open(self.dork_file).readlines())
        self.lock = Lock()
        self.terminal = sys.stdout

    @staticmethod
    def get_engines():
        """Get current engines"""
        return [
            MultiSearcher.ENGINE_BING,
            MultiSearcher.ENGINE_ASK,
            MultiSearcher.ENGINE_RAMBLER
        ]

    def get_links(self, word, engine):
        """Fetch links from engnies"""
        self.links = []
        current_engine = self.engines[engine]

        for ptr in current_engine['page_range']:
            print(current_engine['progress_string'].format(
                ptr, self.ptr_limits[engine], word
            ))

            content = requests.get(
                current_engine['search_string'].format(word, str(ptr))
            )

            if not content.ok:
                pass

            try:
                soup = BeautifulSoup(content.text, 'html.parser')

                for link in soup.find_all('a'):
                    link = link.get('href')

                    if 'http' in link and not re.search(
                        self.exclude_itens, link
                    ):

                        if link not in self.links:
                            self.links.append(link)
                            with self.lock:
                                with open(self.output, 'a+') as fd:
                                    fd.write(link + '\n')
            except Exception:
                pass
    
    def search(self, word):
        for engine in MultiSearcher.get_engines():
            self.get_links(word, engine)    
        
        print("Finished!")

    def main(self):
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for word in open(self.dork_file):
                executor.submit(self.search, word)


if __name__ == "__main__":
    banner = """
      __  __       _ _   _  _____                     _
     |  \/  |     | | | (_)/ ____|                   | |
     | \  / |_   _| | |_ _| (___   ___  __ _ _ __ ___| |__   ___ _ __
     | |\/| | | | | | __| |\___ \ / _ \/ _` | '__/ __| '_ \ / _ \ '__|
     | |  | | |_| | | |_| |____) |  __/ (_| | | | (__| | | |  __/ |
     |_|  |_|\__,_|_|\__|_|_____/ \___|\__,_|_|  \___|_| |_|\___|_|
    """

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
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = parser.parse_args()

    if args.dork_file:
        if not os.path.isfile(args.dork_file):
            exit('File {} not found'.format(args.dork_file))

        print(banner)

        multi_searcher = MultiSearcher(
            args.dork_file,
            args.output,
            args.threads
        )
        multi_searcher.main()
