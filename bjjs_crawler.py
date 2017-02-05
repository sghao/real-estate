#!/usr/bin/python
# coding: utf-8

import logging

import bjjs_parser
import web_fetcher


class BjjsCrawler:
    def __init__(self, storage):
        self.log = logging.getLogger("BjjsCrawler")

        self.storage = storage

        self.web_fetcher = web_fetcher.WebFetcher()

    def _crawl_house_list_page(self, page):
        URL_PATTERN = \
            "http://210.75.213.188/shh/portal/bjjs2016/" \
            "audit_house_list.aspx?pagenumber=%d&pagesize=15"
        url = URL_PATTERN % page
        webcontent = self.web_fetcher.fetch(url)

        parser = bjjs_parser.HouseListParser()
        parser.feed(webcontent)
        parser.close()

        house_list = parser.get_house_list()
        self.log.info("Parsed house list, got %d houses.", len(house_list))

        self.log.info("Persisting house list: %s",
                      ", ".join([str(h[0]) for h in house_list]))
        inserted = self.storage.insert_bjjs_house_list(house_list)
        return inserted

    def crawl_house_list(self):
        consecutive_no_new_house_pages = 0
        for page in range(1, 100000):  # Used as infinite.
            self.log.info("Begin crawl house list page: page=%d", page)

            try:
                inserted = self._crawl_house_list_page(page)
            except Exception as e:
                self.log.error("Error while crawling page: %d", page)
                self.log.exception(e)
                continue

            if inserted == 0:
                consecutive_no_new_house_pages += 1
            else:
                consecutive_no_new_house_pages = 0
            if consecutive_no_new_house_pages == 5:
                self.log.info(
                    "No new house inserted for the last 5 consecutive pages. "
                    "I guess we've already crawled the rest, quiting.")
                return

    def _crawl_house_detail_page(self, house_id):
        URL_PATTERN = \
            "http://210.75.213.188/shh/portal/bjjs2016/" \
            "audit_house_detail.aspx?House_Id=%d"
        url = URL_PATTERN % house_id
        webcontent = self.web_fetcher.fetch(url)

        self.log.info("Parsing house detail: %d", house_id)
        parser = bjjs_parser.HouseDetailParser()
        parser.feed(webcontent)
        parser.close()

        house_detail = parser.get_house_detail()
        # Amend the house_id since house detail page doesn't have this.
        house_detail["house_id"] = house_id

        self.log.info("Persisting house detail: %d", house_id)
        self.storage.insert_bjjs_house_detail(house_detail)

    def crawl_house_detail(self):
        house_ids = self.storage.get_bjjs_house_details_to_update()
        self.log.info(
            "Got %d house_ids with rows absent from house_detail table.",
            len(house_ids))

        for house_id in house_ids:
            self.log.info("Begin crawl house detail page: house_id=%d",
                          house_id)

            try:
                self._crawl_house_detail_page(house_id)
            except Exception as e:
                self.log.error("Error while crawling house detail page: %d",
                               house_id)
                self.log.exception(e)
