#!/usr/bin/python
# coding: utf-8

import logging
import os
import random
import re
import subprocess
import time
import urllib2

import lianjia_parser


def fetch_webcontent(url):
    time.sleep(random.randint(60, 120))  # rate control

    if os.path.exists("webpage"):
        os.remove("webpage")

    # TODO(sghao): Is there a more lightweight way to fetch webpage with
    # cookie?
    subprocess.call([
        "wget",
        "--load-cookies",
        "cookies.txt",  # You can get this from firefox Export Cookies.
        "-O",
        "webpage",
        url,
    ])
    with open("webpage", "r") as f:
        content = f.read()
    return content


class LianjiaCrawler:
    SEED_DISTRICTS = [
        "dongcheng",
        "xicheng",
        "chaoyang",
        "haidian",
        "fengtai",
        "shijingshan",
        "tongzhou",
        "changping",
        "daxing",
        "yizhuangkaifaqu",
        "shunyi",
        "fangshan",
        "mentougou",
        "pinggu",
        "huairou",
        "miyun",
        "yanqing",
        "yanjiao",
    ]

    URL_PATTERN = "http://bj.lianjia.com/ershoufang/%(district)s/%(page)sco32/"

    def __init__(self, storage):
        self.log = logging.getLogger("LianjiaCrawler")

        self.storage = storage

    def _crawl_house_list_page(self, district, page):
        self.log.info("Crawling house list from seed, page: %s, %d",
                      district, page)

        url = LianjiaCrawler.URL_PATTERN % {
            "district": district,
            "page": "pg%d" % page,
        }

        webcontent = fetch_webcontent(url)
        parser = lianjia_parser.HouseListParser()
        parser.feed(webcontent)
        parser.close()

        house_list = parser.get_house_list()
        inserted = self.storage.insert_lianjia_house_list(house_list)
        self.log.info("Parsed %d house, persisted %d.",
                      len(house_list), inserted)
        return inserted

    def crawl_house_list(self):
        for seed_district in LianjiaCrawler.SEED_DISTRICTS:
            self.log.info("Crawling house list from seed: " + seed_district)

            # Get number of pages starting from this seed.
            url = LianjiaCrawler.URL_PATTERN % {
                "district": seed_district,
                "page": "",
            }
            text = fetch_webcontent(url)
            house_list_count = int(re.search(r"count: (\d+),", text).group(1))
            self.log.info("Total houses on list: %d", house_list_count)
            # They have 30 houses per page.
            num_pages = (house_list_count + 29) / 30
            self.log.info("Total pages to crawl: %d", num_pages)
            if num_pages > 100:
                num_pages = 100
                self.log.warning(
                    "Number of pages exceeded 100, capping to 100 as lianjia"
                    " service does.")

            for page in range(1, num_pages + 1):
                try:
                    inserted = self._crawl_house_list_page(seed_district, page)
                except Exception as e:
                    self.log.error("Error while crawling page: %s, %d",
                                   seed_district, page)
                    self.log.exception(e)
                    continue

                if page >= 5 and inserted == 0:
                    self.log.info(
                        "I believe we've crawled all remaining pages, skipping"
                        " the rest of pages and move on to next seed.")
                    break

    def crawl(self):
        self.crawl_house_list()
