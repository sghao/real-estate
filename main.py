#!/usr/bin/python
# coding: utf-8

import argparse
import logging
import logging.config
import os
import random
import sys
import time
import urllib2

import bjjs_parser
import lianjia_crawler
import mysql_storage


URL_PATTERN = "http://210.75.213.188/shh/portal/bjjs2016/audit_house_list.aspx?pagenumber=%d&pagesize=10"

log = None


def parse_args():
    log.info("parsing args")
    parser = argparse.ArgumentParser(
        description="real estate transaction crawler")

    parser.add_argument("--action",
                        choices=[
                            "crawl_bjjs_house_list",
                            "crawl_bjjs_house_detail",
                            "crawl_lianjia",
                        ])

    parser.add_argument("--persistent_storage", choices=["mysql"],
                        default=["mysql"], help="Persistent storage type")

    # When --persistent_storage is mysql, specify host/user/password.
    parser.add_argument("--mysql_hostname", default="localhost")
    parser.add_argument("--mysql_username")
    parser.add_argument("--mysql_password")
    parser.add_argument("--mysql_database", default="real_estate")

    return parser.parse_args()


def init_localdir():
    if not os.path.exists("data"):
        os.mkdir("data")


def init_storage(args):
    if args.persistent_storage == "mysql":
        return mysql_storage.MysqlStorage(
                args.mysql_hostname,
                args.mysql_username,
                args.mysql_password,
                args.mysql_database)


def fetch_webcontent(url):
    webcontent = urllib2.urlopen(url).read()
    return webcontent


def crawl_bjjs_house_list_page(page, storage):
    url = URL_PATTERN % page
    webcontent = fetch_webcontent(url)

    parser = bjjs_parser.HouseListParser()
    parser.feed(webcontent)
    parser.close()

    house_list = parser.get_house_list()
    log.info("Parsed house list, got %d houses.", len(house_list))

    log.info("Persisting house list: %s",
             ", ".join([str(h[0]) for h in house_list]))
    return storage.insert_bjjs_house_list(house_list)


def crawl_bjjs_house_list(args):
    init_localdir()
    storage = init_storage(args)

    consecutive_no_new_house_pages = 0
    for page in range(1, 100000):  # Used as infinite.
        log.info("Begin crawl house list page: page=%d", page)

        try:
            inserted = crawl_bjjs_house_list_page(page, storage)
        except Exception as e:
            log.error("Error while crawling page: %d", page)
            log.exception(e)
            continue

        if inserted == 0:
            consecutive_no_new_house_pages += 1
        else:
            consecutive_no_new_house_pages = 0
        if consecutive_no_new_house_pages == 5:
            log.info("No new house inserted for the last 5 consecutive pages. "
                     "I guess we've already crawled the rest, quiting.")
            return

        log.info("Sleeping between crawl.")
        time.sleep(random.randint(3, 10))


def crawl_bjjs_house_detail(args):
    init_localdir()
    storage = init_storage(args)

    house_ids = storage.get_bjjs_house_details_to_update()
    log.info("Got %d house_ids with rows absent from house_detail table.",
             len(house_ids))

    for house_id in house_ids:
        log.info("Begin crawl house detail page: house_id=%d", house_id)

        url = "http://210.75.213.188/shh/portal/bjjs2016/audit_house_detail.aspx?House_Id=%d" % house_id
        webcontent = fetch_webcontent(url)

        log.info("Parsing house detail: %d", house_id)
        parser = bjjs_parser.HouseDetailParser()
        parser.feed(webcontent)
        parser.close()

        house_detail = parser.get_house_detail()
        # Amend the house_id since house detail page doesn't have this.
        house_detail["house_id"] = house_id
        log.info("Parsed house detail: %d", house_id)

        log.info("Persisting house detail: %d", house_id)
        storage.insert_bjjs_house_detail(house_detail)

        log.info("Sleeping between crawl.")
        time.sleep(random.randint(3, 10))


def main():
    global log
    logging.config.fileConfig("logging.conf")
    log = logging.getLogger("main")

    args = parse_args()
    storage = init_storage(args)

    # TODO(sghao): Refactor out BjjsCrawler into a separate file, the same
    # way as LianjiaCrawler is implemented. This will simplify main.py.

    if args.action == "crawl_bjjs_house_list":
        crawl_bjjs_house_list(args)
    elif args.action == "crawl_bjjs_house_detail":
        crawl_bjjs_house_detail(args)
    elif args.action == "crawl_lianjia":
        crawler = lianjia_crawler.LianjiaCrawler(storage)
        crawler.crawl()


if __name__ == "__main__":
    main()
