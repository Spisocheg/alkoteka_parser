# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.exceptions import IgnoreRequest, CloseSpider
from browserforge.headers import HeaderGenerator

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class AlkotekaSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # maching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class AlkotekaDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class JSONResponseValidateSpiderMiddleware:
    """Проверяет входящие запросы на соответствие их формату JSON"""

    def __init__(self, settings):
        self.parsing_params = settings.get('PARSING_PARAMS', None)

        if not self.parsing_params:
            raise CloseSpider()

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(crawler.settings)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        if spider.name == 'products_by_category':
            try:
                city_url = self.parsing_params.get(spider.name, None).get('CITY_URL')
                product_url = self.parsing_params.get(spider.name, None).get('PRODUCT_URL')
            except:
                msg = f'В файле settings.py проекта в словаре настройки паука не заполнены CITY_URL и/или PRODUCT_URL'
                raise CloseSpider(msg)

            # Останавливать работу паука, если на запрос списка городов возвращается не json
            #                                                                           - дальнейшая работа невозможна
            if city_url in response.url:
                try:
                    data = response.json().get('results')
                except ValueError:
                    msg = f'Invalid JSON at {response.url}'
                    raise CloseSpider(msg)

            # Игнорировать запрос, если ответ на него - не json
            if product_url in response.url:
                try:
                    data = response.json().get('results')
                except ValueError:
                    msg = f'Invalid JSON at {response.url}'
                    raise IgnoreRequest(msg)

        return None

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class BrowserHeadersReplaceDownloaderMiddleware:
    """Дополняет все requests уникальными данными браузера"""
    
    def __init__(self):
        # Создание генератора headers
        self.generator = HeaderGenerator()

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        # Генерация полный набора headers для каждого запроса
        headers = self.generator.generate()

        # Применение headers к request
        for key, value in headers.items():
            request.headers[key] = value

        return None
