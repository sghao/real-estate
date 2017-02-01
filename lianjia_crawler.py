#!/usr/bin/python
# coding: utf-8

import logging
import random
import time
import urllib2

import lianjia_parser


class LianjiaCrawler:
    def __init__(self, storage):
        self.log = logging.getLogger("LianjiaCrawler")

        self.storage = storage

    def crawl(self):
        url = "http://bj.lianjia.com/ershoufang/haidian/co32/"
        webcontent = urllib2.urlopen(url).read()
        self.log.info("Parsing house list page.")
        parser = lianjia_parser.HouseListParser()
        parser.feed(webcontent)
        parser.close()

        house_list = parser.get_house_list()
        self.log.info("Parsed house list, got %d houses.", len(house_list))

        self.log.info("Persisting house list: %s",
                      ", ".join([str(h["house_id"]) for h in house_list]))
        self.storage.insert_lianjia_house_list(house_list)

        self.log.info("Sleeping between crawl.")
        time.sleep(random.randint(2, 5))
