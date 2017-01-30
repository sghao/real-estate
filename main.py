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

import audit_house_parser
import mysql_storage


URL_PATTERN = "http://210.75.213.188/shh/portal/bjjs2016/audit_house_list.aspx?pagenumber=%d&pagesize=10"

log = None


def parse_args():
    log.info("parsing args")
    parser = argparse.ArgumentParser(
            description="real estate transaction crawler")

    parser.add_argument("--action",
                        choices=["crawl_house_list", "crawl_house_detail"])

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


def crawl_house_list(args):
    init_localdir()
    storage = init_storage(args)

    for page in xrange(1852, 0, -1):
        log.info("Begin crawl house list page: page=%d", page)

        # TODO(sghao): During the Chinese New Year, the service is temporarily
        # unavailable. Switching to local cache to unblock further development.
        # We'll revert this back once service is up.
        # url = URL_PATTERN % page
        # webcontent = fetch_webcontent(url)
        # with open("data/page-%05d" % page, "w") as f:
        #     f.write(webcontent)

        with open("data/page-%05d" % page, "r") as f:
            webcontent = f.read()

        log.info("Parsing house list.")
        parser = audit_house_parser.HouseListParser()
        parser.feed(webcontent)
        parser.close()

        house_list = parser.get_house_list()
        log.info("Parsed house list, got %d houses.", len(house_list))

        log.info("Persisting house list: %s",
                 ", ".join([str(h[0]) for h in house_list]))
        storage.insert_house_list(house_list)

        log.info("Sleeping between crawl.")
        time.sleep(random.randint(3, 10))


def crawl_house_detail(args):
    init_localdir()
    storage = init_storage(args)

    house_ids = storage.get_house_details_to_update()
    log.info("Got %d house_ids with rows absent from house_detail table.",
             len(house_ids))

    for house_id in house_ids:
        log.info("Begin crawl house detail page: house_id=%d", house_id)

        # TODO(sghao): During the Chinese New Year, the service is temporarily
        # unavailable. Using local cache instead for development.
        with open("data/house_detail-%d" % house_id, "r") as f:
            webcontent = f.read()

        log.info("Parsing house detail: %d", house_id)
        parser = audit_house_parser.HouseDetailParser()
        parser.feed(webcontent)
        parser.close()

        house_detail = parser.get_house_detail()
        # Amend the house_id since house detail page doesn't have this.
        house_detail["house_id"] = house_id
        log.info("Parsed house detail: %d", house_id)

        log.info("Persisting house detail: %d", house_id)
        storage.insert_house_detail(house_detail)

        log.info("Sleeping between crawl.")
        time.sleep(random.randint(3, 10))


def main():
    global log
    logging.config.fileConfig("logging.conf")
    log = logging.getLogger("main")

    args = parse_args()

    if args.action == "crawl_house_list":
        crawl_house_list(args)
    elif args.action == "crawl_house_detail":
        crawl_house_detail(args)


if __name__ == "__main__":
    main()
