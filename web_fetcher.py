#!/usr/bin/python
# coding: utf-8

import logging
import os
import random
import subprocess
import tempfile
import time


class WebFetcher:
    """ Helper class for fetching webpage with http request.

    TODO(sghao): Implemented with subprocess and wget, but is there a more
    lightweight way to fetch webpage with cookie support?
    """
    def __init__(self):
        self.log = logging.getLogger("WebFetcher")

    def get(self, url):
        self._rate_control(url)

        with tempfile.NamedTemporaryFile(
                prefix="web_fetcher_webcontent_", delete=False) as f:
            tmp_filepath = f.name

        subprocess.call([
            "wget",
            "--load-cookies", "cookies.txt",  # Get from firefox Export Cookies.
            "--output-document", tmp_filepath,
            url,
        ])
        with open(tmp_filepath, "r") as f:
            content = f.read()
        os.remove(tmp_filepath)
        return content

    def post(self,
             url,
             request_body,
             add_headers=[]):
        self._rate_control(url)

        with tempfile.NamedTemporaryFile(
                prefix="web_fetcher_", delete=False) as f:
            tmp_filepath = f.name

        # Write request body to a temp file.
        with tempfile.NamedTemporaryFile(
                prefix="web_fetcher_post_request_body_", delete=False) as f:
            request_body_filepath = f.name
            f.write(request_body)

        # Prepare additional headers.
        headers_args = []
        for header in add_headers:
            headers_args.append("--header")
            headers_args.append(header)

        subprocess.call([
            "wget",
            "--load-cookies", "cookies.txt",  # Get from firefox Export Cookies.
            "--output-document", tmp_filepath,
            "--post-file", request_body_filepath,
            "--header", "Content-Length: %d" % len(request_body),
        ] + headers_args + [
            url,
        ])
        os.remove(request_body_filepath)

        with open(tmp_filepath, "r") as f:
            content = f.read()
        os.remove(tmp_filepath)
        return content

    def _rate_control(self, url):
        """Simple rate control policy implementation.

        bjjs: sleep 3~10 seconds
        lianjia: sleep 60~120 seconds

        TODO(sghao): Better and more flexible rate control policy in future.
        """
        sleep_seconds = 30  # default sleep
        if "210.75.213.188" in url:
            sleep_seconds = random.randint(3, 10)
        elif "lianjia.com" in url:
            sleep_seconds = random.randint(60, 120)

        self.log.info("Sleep %d seconds for rate control.", sleep_seconds)
        time.sleep(sleep_seconds)
