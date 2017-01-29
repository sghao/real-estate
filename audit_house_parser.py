#!/usr/bin/python
# coding: utf-8

import logging
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


class HouseDetailParser(HTMLParser.HTMLParser):
    # Tuple(name, mysql column name, column type, regex for value
    # extraction)
    HOUSE_DETAIL_SCHEMA = [
        ("核验编号", "verification_id", str, ".*"),
        ("区　　县", "district", str, ".*"),
        ("小　　区", "compound_name", str, ".*"),
        ("朝　　向", "house_orientation", str, ".*"),
        ("户　　型", "house_layout", str, ".*"),
        ("建筑面积", "house_area", float, r"[\d\.]+"),
        ("所在楼层", "house_floor", str, ".*"),
        ("总 层 数", "house_total_floor", str, ".*"),
        ("建成年代", "completion_year", int, r"\d+"),
        ("规划用途", "planned_use", str, ".*"),
        ("装修情况", "decoration", str, ".*"),
        ("拟售价格", "proposed_price", float, r"[\d\.]+"),
        ("经纪机构", "agency", str, ".*"),
        ("联系电话", "agency_phone", str, ".*"),
        ("经 纪 人", "agent", str, ".*"),
        ("联系电话", "agent_phone", str, ".*"),
        ("所有权状态", "ownership_state", str, ".*"),
        ("抵押状态", "mortgage_state", str, ".*"),
        ("查封状态", "seal_state", str, ".*"),
    ]

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)

        self.log = logging.getLogger("HouseDetailParser")

        self.tbody_depth = 0
        self.last_tag = None
        self.house_detail_raw = []

    def get_house_detail(self):
        house_detail = {}

        # House detail paired with schema.
        pairs = zip(self.house_detail_raw,
                    HouseDetailParser.HOUSE_DETAIL_SCHEMA)
        for ((key, value), schema) in pairs:
            if key <> schema[0]:
                self.log.error(
                    "Unexpected column from house detail: %s, %s, %s",
                    key, schema, self.house_detail_raw)

            value = re.search(schema[3], value).group()
            house_detail[schema[1]] = schema[2](value)

        return house_detail

    def handle_starttag(self, tag, attrs):
        self.tbody_depth += 1 if tag == "tbody" else 0
        self.last_tag = tag

    def handle_endtag(self, tag):
        self.tbody_depth -= 1 if tag == "tbody" else 0

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        if self.last_tag == "th":
            self.house_detail_raw.append([data])
        elif self.last_tag == "td":
            self.house_detail_raw[-1].append(data)
