#!/usr/bin/python
# coding: utf-8

from HTMLParser import HTMLParser


class HouseListParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.path = []
        self.tbody_count = 0
        self.house_list = []

    def handle_starttag(self, tag, attrs):
        if tag == "tbody":
            self.tbody_count += 1

        if self.tbody_count == 2 and tag == "tr":
            self.house_list.append([])

        if self.tbody_count == 2 and tag == "a":
            self.house_list[-1].append(attrs[0][1])

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        if self.tbody_count == 2:
            self.house_list[-1].append(data)
