#!/usr/bin/python
# coding: utf-8

import os
import random
import sys
import time
import urllib2

import house_list_parser


URL_PATTERN = "http://210.75.213.188/shh/portal/bjjs2016/audit_house_list.aspx?pagenumber=%d&pagesize=10"


def init():
    if not os.path.exists("data"):
        os.mkdir("data")


def fetch_webcontent(url):
    webcontent = urllib2.urlopen(url).read()
    return webcontent


def main():
    init()

    for page in xrange(1856, 0, -1):
        sys.stderr.write("Page: %d\n" % page)

        url = URL_PATTERN % page
        webcontent = fetch_webcontent(url)
        with open("data/page-%05d" % page, "w") as f:
            f.write(webcontent)

        parser = house_list_parser.HouseListParser()
        parser.feed(webcontent)
        parser.close()
        print "\n".join(["\t".join(h) for h in parser.house_list])

        time.sleep(random.randint(3, 10))


if __name__ == "__main__":
    main()
