from functools import lru_cache # Кэш для нашего сервера
from urllib.parse import parse_qs, urlparse # Парсинг запросов

class Request:
    def __init__(self, method, target, version, headers, rfile):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self.rfile = rfile

    @property
    def path(self):
        return self.url.path

    @property
    @lru_cache(None) # Кэш (декоратор)
    def query(self):
        return parse_qs(self.url.query)

    @property
    @lru_cache(None)
    def url(self):
        return urlparse(self.target)