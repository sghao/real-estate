#!/usr/bin/python
# coding: utf-8

import datetime
import logging
import re

import HTMLParser

class HouseListParser(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)

        self.log = logging.getLogger("lianjia_parser.HouseListParser")

        self.path = []
        self.house_ids = []
        self.house_list_raw = []

    def handle_starttag(self, tag, attrs):
        self.path.append(tag)

        # Parse house_id from the link that references to house detail page.
        d = dict(attrs)
        if ("href" in d and "data-log_index" in d and
                "class" in d and d["class"] == "title"):
            index = int(d["data-log_index"]) - 1
            house_id = int(re.search("\d+", d["href"]).group())

            assert index == len(self.house_ids)
            self.house_ids.append(house_id)

    def handle_endtag(self, tag):
        self.path.pop()

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        # We extract house list information by looking for tag pattern:
        #   "*.dd.ul.(li.){N+1}a.div.div*"
        # N is the index of house in the list.

        # TODO(sghao): Is there a better way to find a subarray from an array?
        path_str = ".".join(self.path)
        pos = path_str.find("dd.ul.li.")
        if pos == -1:
            return

        path_str = path_str[pos + len("dd.ul.li."):]
        count = path_str.count("li.")

        path_str = path_str.lstrip("li.")
        if not path_str.startswith("a.div.div"):
            return
        path_str = path_str.lstrip("a.div.div")

        if len(self.house_list_raw) <= count:
            self.house_list_raw.append([])
        tag_prefix = "tag:" if path_str else ""
        self.house_list_raw[count].append(tag_prefix + data)

    def get_house_list(self):
        return [
            self._parse_house_raw(house_id, raw)
                for house_id, raw in zip(self.house_ids, self.house_list_raw)]

    def _parse_house_raw(self, house_id, raw):
        """ Parsing raw data into schemaful house object.

        Example raw = [
          强佑清河新城 1室0厅 435万
          强佑清河新城
          | 1室0厅 | 62.4平米 | 北 | 简装 | 有电梯
          低楼层(共22层)2009年建板塔结合  -
          清河
          9人关注 / 共0次带看 / 8天以前发布
          tag:距离8号线永泰庄站1119米
          tag:房本满五年
          tag:435
          万
          tag:单价69712元/平米
          tag:关注
        ]

        Parsed and returned result: {
          asking_total_price: 435
          asking_unit_price: 69712
          building_type: 板塔结合
          completion_year: 2009
          compound_name: 强佑清河新城
          crawled_date: 2017-02-01
          decoration: 简装
          elevator: 有电梯
          followers_count: 9
          house_area: 62.4
          house_id: 101101096272
          house_layout: 1室0厅
          house_orientation: 北
          house_total_floor: 22
          location_near: 距离8号线永泰庄站1119米
          posted_date: 2017-01-24
          region: 清河
          tags: |房本满五年
          visitors_count: 0
        }
        """
        house = {"house_id": house_id}

        non_tag = [s for s in raw if not s.startswith("tag:")]
        house["compound_name"] = non_tag[1]
        # Parse non_tag[3], example values:
        #   "低楼层(共6层)2004年建板楼  -"
        #   "高楼层(共12层)  -"
        #   "-"
        m = re.match(r"^(.*?)(\(共(\d+)层\))*((\d+)年建(.*))*$",
                     non_tag[3].strip(" -"))
        if not m:
            self.log.error("Error in parsing lianjia house list non_tag[3]: " +
                           non_tag[3])
        if m.group(1):
            house["house_floor"] = m.group(1)
        if m.group(3):
            house["house_total_floor"] = int(m.group(3))
        if m.group(5):
            house["completion_year"] = int(m.group(5))
        if m.group(6):
            house["building_type"] = m.group(6)
        house["region"] = non_tag[4]
        # In some case, "有电梯" part in the end is missing, hence
        # subsidizing "|" for parser.
        _0, _1, _2, _3, _4, _5 = [
            s.strip() for s in (non_tag[2] + "|||").split("|")][0:6]
        house["house_layout"] = _1
        house["house_area"] = float(re.search(r"[\d\.]+", _2).group())
        if _3:
            house["house_orientation"] = _3
        if _4:
            house["decoration"] = _4
        if _5:
            house["elevator"] = _5
        # Parse non_tag[5], example values:
        #   "1人关注 / 共0次带看 / 刚刚发布"
        #   "1人关注 / 共0次带看 / 10天以前发布"
        #   "1人关注 / 共0次带看 / 一年前发布"
        m = re.match(
            r"^(\d+)人关注 / 共(\d+)次带看 / (\d*)(.*?)(以)*(前)*发布",
            non_tag[5])
        if not m:
            self.log.error("Error in parsing lianjia house list non_tag[5]: " +
                           non_tag[5])
        house["followers_count"] = int(m.group(1))
        house["visitors_count"] = int(m.group(2))

        # Parse time delta.
        unit = m.group(4)
        if unit == "刚刚":
            days = 0
        elif unit == "天":
            days = int(m.group(3))
        elif unit == "个月":
            days = int(m.group(3)) * 30 + 1
        elif unit == "一年":
            days = 365 + 1

        crawled_date = datetime.date.today()
        posted_date = crawled_date - datetime.timedelta(days=days)
        house["crawled_date"] = str(crawled_date)
        house["posted_date"] = str(posted_date)

        # Tuple(regex, column name, column type)
        TAG_SCHEMA = [
            ("(距离.*)", "location_near", str),
            (r"(\d+)", "asking_total_price", int),
            (r"单价(\d+)元/平米", "asking_unit_price", int),
            ("关注", "", None),
        ]

        tags = [s[len("tag:"):] for s in raw if s.startswith("tag:")]
        for text in tags:
            matched = False
            for column in TAG_SCHEMA:
                m = re.match(column[0], text)
                if m:
                    if column[1]:
                        house[column[1]] = column[2](m.group(1))
                    matched = True
                    break

            if not matched:
                house.setdefault("tags", "")
                house["tags"] += "|%s" % text

        return house
