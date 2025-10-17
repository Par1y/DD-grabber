"""Scrapy pipeline 示例：将 item POST 到本地 HTTP collector。

在 Scrapy 项目的 settings.py 中启用：
ITEM_PIPELINES = {
    'yourproject.pipelines.HttpPostPipeline': 300,
}

并配置：
HTTP_COLLECTOR_URL = 'http://localhost:8080/items'

此 pipeline 使用 requests 库进行同步 HTTP 调用，简单可靠。可根据需要改为异步（aiohttp）以提高吞吐。
"""
import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HttpPostPipeline:
    def __init__(self, collector_url):
        self.collector_url = collector_url
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.3, status_forcelist=(500,502,503,504))
        session.mount('http://', HTTPAdapter(max_retries=retries))
        self._session = session

    @classmethod
    def from_crawler(cls, crawler):
        url = crawler.settings.get('HTTP_COLLECTOR_URL', 'http://localhost:8080/items')
        return cls(url)

    def process_item(self, item, spider):
        try:
            resp = self._session.post(self.collector_url, json=dict(item), timeout=5)
            resp.raise_for_status()
        except Exception as e:
            spider.logger.error(f"Failed to post item to collector: {e}")
        return item
