#!/usr/bin/python
# coding: utf-8

import argparse
import logging
import logging.config
import os

import bjjs_crawler
import lianjia_crawler
import mysql_storage


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


def init_storage(args):
    if args.persistent_storage == "mysql":
        return mysql_storage.MysqlStorage(
                args.mysql_hostname,
                args.mysql_username,
                args.mysql_password,
                args.mysql_database)


def main():
    global log
    logging.config.fileConfig("logging.conf")
    log = logging.getLogger("main")

    args = parse_args()
    storage = init_storage(args)

    if args.action == "crawl_bjjs_house_list":
        crawler = bjjs_crawler.BjjsCrawler(storage)
        crawler.crawl_house_list()
    elif args.action == "crawl_bjjs_house_detail":
        crawler = bjjs_crawler.BjjsCrawler(storage)
        crawler.crawl_house_detail()
    elif args.action == "crawl_lianjia":
        crawler = lianjia_crawler.LianjiaCrawler(storage)
        crawler.crawl()


if __name__ == "__main__":
    main()
