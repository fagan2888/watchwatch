from bs4 import BeautifulSoup
import logging
import json
import pickledb
from random import randint
import requests
from time import sleep


def load_params(fname='settings.json'):
    return json.load(open(fname, 'r'))


def load_db(fname='watch.pkldb'):
    return pickledb.load(fname, True)


class Thread(object):
    def __init__(self, tag):
        self.tag = tag

    def is_sticky(self):
        return 'sticky' in self.tag.attrs['class']

    def get_posts(self):
        return int(self.tag.find(class_='stats').find(class_='major').text.split(' ')[1])

    def get_id(self):
        return self.tag.attrs['id']

    def get_link(self):
        for link in self.tag.find_all('a'):
            if 'data-previewurl' in link.attrs:
                return link.attrs['href']

    def get_title(self):
        for link in self.tag.find_all('a'):
            if 'data-previewurl' in link.attrs:
                return link.text

    def is_new(self, db):
        """ returns true if the thread is new"""
        return db.get(self.get_id()) is None

    def is_updated(self, db):
        """ returns true if the thread has been updated"""
        return db.get(self.get_id()) != self.get_posts()

    def __repr__(self):
        return self.get_id()

    def __str__(self):
        return self.get_title()


def get_threads(params):
    headers = {'User-Agent': params['user_agent']}
    resp = requests.get(params['sales_url'], headers=headers)
    soup = BeautifulSoup(resp.text, 'html5lib')

    threads = [
        Thread(tag) for tag in soup.findAll('li', class_='discussionListItem')
    ]
    return list(filter(lambda x: not x.is_sticky(), threads))


def print_main():
    logger = logging.getLogger(__name__)
    params = load_params()
    db = pickledb.load(params['pickledb_file'], True)

    for thread in get_threads(params):
        if thread.is_new(db):
            logger.info("NEW THREAD:\n\t{}\n\t{}\n\n".format(
                thread.get_title(),
                "{}{}".format(params['base_url'], thread.get_link())))

        elif thread.is_updated(db):
            logger.info("UPDATED THREAD:\n\t{}\n\t{}\n\n".format(
                thread.get_title(),
                "{}{}".format(params['base_url'], thread.get_link())))

        db.set(thread.get_id(), thread.get_posts())
    db.dump()  # redundant


def init_logging(params):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    log_format = logging.Formatter("%(asctime)s: %(message)s")

    if 'log_file' in params:
        file_handler = logging.FileHandler(params['log_file'])
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(log_format)
    logger.addHandler(stream_handler)


def loop_main():
    logger = logging.getLogger(__name__)
    try:
        while True:
            print_main()
            sleep_dur = randint(60, 60*10)
            logger.info("sleeping {} seconds".format(sleep_dur))
            sleep(sleep_dur)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    params = load_params()
    init_logging(params)
    loop_main()
