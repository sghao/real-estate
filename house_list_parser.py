#!/usr/bin/python
# coding: utf-8

import re

import HTMLParser


class HouseListParser(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.path = []
        self.tbody_depth = 0
        self.house_list_text = []

    def get_house_list(self):
        return [self._parse_house_text(h) for h in self.house_list_text if h]

    def handle_starttag(self, tag, attrs):
        if tag == "tbody":
            self.tbody_depth += 1

        if self.tbody_depth == 2 and tag == "tr":
            self.house_list_text.append([])

        if self.tbody_depth == 2 and tag == "a":
            self.house_list_text[-1].append(attrs[0][1])

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        if self.tbody_depth == 2:
            self.house_list_text[-1].append(data)

    def _parse_house_text(self, house_text):
        return [
                int(house_text[0]),
                house_text[1],
                house_text[2],
                house_text[3],
                float(house_text[4]),
                float(re.search(r"(\d+)", house_text[5]).group(1)),
                house_text[6],
                house_text[7],
                re.search(r"House_Id=(\d+)", house_text[8]).group(1),
        ]
