#!/usr/bin/python
# coding: utf-8

import logging
import os
import random
import subprocess
import tempfile
import time


class WebFetcher:
    def __init__(self):
        self.log = logging.getLogger("WebFetcher")

    def fetch(self, url):
        self._rate_control(url)

        with tempfile.NamedTemporaryFile(
                suffix=".tmp", prefix="web_fetcher_", delete=False) as f:
            tmp_filename = f.name

        # TODO(sghao): Is there a more lightweight way to fetch webpage with
        # cookie?
        subprocess.call([
            "wget",
            "--load-cookies", "cookies.txt",  # Get from firefox Export Cookies.
            "--output-document", tmp_filename,
            url,
        ])
        with open(tmp_filename, "r") as f:
            content = f.read()
        os.remove(tmp_filename)
        return content

    def _rate_control(self, url):
        """Simple rate control implementation.

        bjjs: sleep 3~10 seconds
        lianjia: sleep 60~120 seconds

        TODO(sghao): Better and more flexible rate control policy in future.
        """
        sleep_seconds = 30  # default sleep
        print url
        if "210.75.213.188" in url:
            sleep_seconds = random.randint(3, 10)
        elif "lianjia.com" in url:
            sleep_seconds = random.randint(60, 120)

        self.log.info("Sleep %d seconds for rate control.", sleep_seconds)
        time.sleep(sleep_seconds)
