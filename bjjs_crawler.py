#!/usr/bin/python
# coding: utf-8

import datetime
import logging
import re

import bjjs_parser
import web_fetcher


class BjjsCrawler:
    def __init__(self, storage):
        self.log = logging.getLogger("BjjsCrawler")

        self.storage = storage

        self.web_fetcher = web_fetcher.WebFetcher()

    def crawl_house_list(self):
        """Crawl all house list.

        We start from yesterday's date and loop backward, crawling most recent
        date's list first. End crawling when we get to a date in which all
        houses have already been crawled, which might suggest the starting
        date of previous crawl.
        """
        date = datetime.date.today()
        while True:
            self.log.info("Begin crawling date: %s", date)
            total_parsed_house, total_updated_house = \
                self._crawl_house_list_with_filters({"date": date})
            self.log.info(
                "Finished crawling date: "
                "date=%s,total_parsed_house=%d,total_updated_house=%d",
                date, total_parsed_house, total_updated_house)

            if total_parsed_house != 0 and total_updated_house == 0:
                self.log.info("No new house found in date %s, stopping here.",
                              date)
                break

            date = date - datetime.timedelta(days=1)

    def _crawl_house_list_with_filters(self, filters):
        """Crawl all house list using given filters.

        Supported filters:
            "date": "yyyy-mm-dd"
        """
        self.log.info("Crawl all house list pages with filters: %s", filters)

        # Using given filter condition, get first page of navigation with
        # post request.
        with open("bjjs_request_body", "r") as f:
            request_body = f.read()
        request_body = request_body % filters

        URL_HOME = "http://210.75.213.188/shh/portal/bjjs2016/" \
                   "audit_house_list.aspx"
        BOUNDARY = "----WebKitFormBoundaryp2YEic9nyL7LewNv"
        webcontent = self.web_fetcher.post(
            url=URL_HOME,
            request_body=request_body,
            add_headers=[
                "Content-Type: multipart/form-data; boundary=%s" % BOUNDARY,
            ],
        )

        # Parse number of pages.
        total_pages = int(
            re.search(r"页次：\d+/(\d+)页", webcontent).group(1))
        self.log.info("Total pages to crawl: %d", total_pages)

        # Parse the first page.
        total_parsed_house, total_updated_house = \
            self._process_house_list_page(webcontent)

        # Now crawl the rest of pages.
        for page in range(2, total_pages + 1):
            self.log.info("Crawling page %d/%d.", page, total_pages)

            URL_PATTERN = \
                "http://210.75.213.188/shh/portal/bjjs2016/" \
                "audit_house_list.aspx?pagenumber=%d&pagesize=10"
            url = URL_PATTERN % page

            try:
                webcontent = self.web_fetcher.get(url)
                parsed_house, updated_house = \
                    self._process_house_list_page(webcontent)
                total_parsed_house += parsed_house
                total_updated_house += updated_house
            except Exception as e:
                self.log.error("Error while crawling page: %d", page)
                self.log.exception(e)
                continue

        return total_parsed_house, total_updated_house

    def _process_house_list_page(self, webcontent):
        """Parse and persist houses from house list webpage."""
        parser = bjjs_parser.HouseListParser()
        parser.feed(webcontent)
        parser.close()

        house_list = parser.get_house_list()
        self.log.info("Parsed house list, got %d houses.", len(house_list))

        self.log.info("Persisting house list: %s",
                      ", ".join([str(h[0]) for h in house_list]))
        updated_house = self.storage.insert_bjjs_house_list(house_list)
        return len(house_list), updated_house

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

    def _crawl_house_detail_page(self, house_id):
        URL_PATTERN = \
            "http://210.75.213.188/shh/portal/bjjs2016/" \
            "audit_house_detail.aspx?House_Id=%d"
        url = URL_PATTERN % house_id
        webcontent = self.web_fetcher.get(url)

        self.log.info("Parsing house detail: %d", house_id)
        parser = bjjs_parser.HouseDetailParser()
        parser.feed(webcontent)
        parser.close()

        house_detail = parser.get_house_detail()
        # Amend the house_id since house detail page doesn't have this.
        house_detail["house_id"] = house_id

        self.log.info("Persisting house detail: %d", house_id)
        self.storage.insert_bjjs_house_detail(house_detail)
