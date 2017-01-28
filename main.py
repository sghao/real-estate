#!/usr/bin/python
# coding: utf-8

import os
import random
import sys
import time
import urllib2

import house_list_parser
import mysql_storage


URL_PATTERN = "http://210.75.213.188/shh/portal/bjjs2016/audit_house_list.aspx?pagenumber=%d&pagesize=10"


def init():
    if not os.path.exists("data"):
        os.mkdir("data")


def fetch_webcontent(url):
    webcontent = urllib2.urlopen(url).read()
    return webcontent


def main():
    init()

    # TODO(sghao): Find a better way to pass (or config) username/password.
    storage = mysql_storage.MysqlStorage("localhost", "********", "********", "real_estate")

    for page in xrange(1852, 0, -1):
        sys.stderr.write("Page: %d\n" % page)

        # TODO(sghao): During the Chinese New Year, the service is temporarily
        # unavailable. Switching to local cache to unblock further development.
        # We'll revert this back once service is up.
        # url = URL_PATTERN % page
        # webcontent = fetch_webcontent(url)
        # with open("data/page-%05d" % page, "w") as f:
        #     f.write(webcontent)

        with open("data/page-%05d" % page, "r") as f:
            webcontent = f.read()

        parser = house_list_parser.HouseListParser()
        parser.feed(webcontent)
        parser.close()

        house_list = parser.get_house_list()
        storage.insert_house_list(house_list)

        time.sleep(random.randint(3, 10))


if __name__ == "__main__":
    main()
