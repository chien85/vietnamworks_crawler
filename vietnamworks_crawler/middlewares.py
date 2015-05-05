from scrapy.exceptions import IgnoreRequest
from scrapy import log
from scrapy.http import Request
from scrapy.item import BaseItem
from scrapy.utils.request import request_fingerprint
from vietnamworks_crawler.items import JobItem
from urlparse import urlparse
from scrapy.utils.python import WeakKeyCache

# http://snipplr.com/view/67018/middleware-to-avoid-revisiting-already-visited-items/
class IgnoreVisitedItems(object):
    """Middleware to ignore re-visiting item pages if they were already visited
    before. The requests to be filtered by have a meta['filter_visited'] flag
    enabled and optionally define an id to use for identifying them, which
    defaults the request fingerprint, although you'd want to use the item id,
    if you already have it beforehand to make it more robust.
    """

    FILTER_VISITED = 'filter_visited'
    VISITED_ID = 'visited_id'
    CONTEXT_KEY = 'visited_ids'

    def process_spider_output(self, response, result, spider):
        context = getattr(spider, 'context', {})
        visited_ids = context.setdefault(self.CONTEXT_KEY, {})
        ret = []
        for x in result:
            visited = False
            if isinstance(x, Request):
                if self.FILTER_VISITED in x.meta:
                    visit_id = self._visited_id(x)
                    if visit_id in visited_ids:
                        log.msg("Ignoring already visited: %s" % x.url,
                                level=log.INFO, spider=spider)
                        visited = True
            elif isinstance(x, BaseItem):
                visit_id = self._visited_id(response.request)
                if visit_id:
                    visited_ids[visit_id] = True
                    x['visit_id'] = visit_id
                    x['visit_status'] = 'new'
            if visited:
                ret.append(MyItem(visit_id=visit_id, visit_status='old'))
            else:
                ret.append(x)
        return ret

    def _visited_id(self, request):
        return request.meta.get(self.VISITED_ID) or request_fingerprint(request)
        #return request.meta.get(self.VISITED_ID) or request_fingerprint(request)

class GoogleCacheMiddleware(object):
    """
        https://github.com/scrapy/scrapy/issues/280
        this middleware allow spider to crawl the spicific domain url in google caches.

        you can define the GOOGLE_CACHE_DOMAINS in settings,it is a list which you want to
        visit the google cache.Or you can define a google_cache_domains in your spider and it
        is as the highest priority.
    """
    google_cache = 'http://webcache.googleusercontent.com/search?q=cache:'

    def __init__(self, cache_domains=''):
        self.cache = WeakKeyCache(self._cache_domains)
        self.cache_domains = cache_domains

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings['GOOGLE_CACHE_DOMAINS'])

    def _cache_domains(self, spider):
        if hasattr(spider, 'google_cache_domains'):
            return spider.google_cache_domains
        elif self.cache_domains:
            return self.cache_domains

        return ""

    def process_request(self, request, spider):
        """
            the scrapy documention said that:
                If it returns a Request object, the returned request will be rescheduled (in the
                Scheduler) to be downloaded in the future. The callback of the original request
                will always be called. If the new request has a callback it will be called with the
                response downloaded, and the output of that callback will then be passed to
                the original callback. If the new request doesn't have a callback, the response
                downloaded will be just passed to the original request callback.

            but actually is that if it returns a Request object,then the original request will be
            droped,so you must make sure that the new request object's callback is the original callback.
        """
        gcd = self.cache[spider]
        if gcd:
            if urlparse(request.url).netloc in gcd:
                request = request.replace(url=self.google_cache + request.url)
                request.meta['google_cache'] = True
                return request

    def process_response(self, request, response, spider):

        if request.meta.get('google_cache',False):
            return response.replace(url = response.url[len(self.google_cache):])

        return response
