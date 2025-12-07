# Scrapy settings for alkoteka project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import pathlib


# Константа пути к корневой папке проекта
PROJECT_DIR_PATH = pathlib.Path(__file__).parent.parent.parent


BOT_NAME = "alkoteka"

SPIDER_MODULES = ["alkoteka.spiders"]
NEWSPIDER_MODULE = "alkoteka.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "alkoteka (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
   # "alkoteka.middlewares.AlkotekaSpiderMiddleware": 543,
   "alkoteka.middlewares.JSONResponseValidateSpiderMiddleware": 500,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # "alkoteka.middlewares.AlkotekaDownloaderMiddleware": 543,
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "alkoteka.middlewares.BrowserHeadersReplaceDownloaderMiddleware": 400,
    "rotating_proxies.middlewares.RotatingProxyMiddleware": 610,
    "rotating_proxies.middlewares.BanDetectionMiddleware": 620,
}

# Настройки scrapy-rotating-proxies
ROTATING_PROXY_LIST_PATH = PROJECT_DIR_PATH / 'proxies.txt'
ROTATING_PROXY_PAGE_RETRY_TIMES = 5
ROTATING_PROXY_CLOSE_SPIDER = False                             # True для остановки сбора при исчерпании прокси

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    # "alkoteka.pipelines.AlkotekaPipeline": 300,
    "alkoteka.pipelines.FormatingFieldsPipeline": 400,
    "alkoteka.pipelines.ValidateFieldsPipeline": 500,
    # до 550 вкл - input преобразование, после (551+) - output преобразование
    "alkoteka.pipelines.RenameFieldsPipeline": 600,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"


# Константа пути к файлу со ссылками для сбора данных
URLS_FILENAME = PROJECT_DIR_PATH / 'links.txt'

# Настройки для сбора данных
PARSING_PARAMS = {
    'products_by_category': {
        'PER_PAGE': 20,                     # Количество товаров на странице
        'DEFAULT_CITY_NAME': 'Краснодар',   # Город по умолчанию для сбора данных
        'CITY_URL': 'https://alkoteka.com/web-api/v1/city?city_uuid=396df2b5-7b2b-11eb-80cd-00155d039009',
        'PRODUCT_URL': 'https://alkoteka.com/web-api/v1/product',
        'REFERER_URL': 'https://alkoteka.com'
    }
}

# Форматы:
# spider.name : {
#   'old_field_name': 'new_field_name',
#   'parent_field': {
#       'old_field_name': 'new_field_name'
# }
# Поддерживает только 2 уровня вложенности
RENAME_PATTERN = {
    'products_by_category': {
        'metadata': {
            'description': '__description'
        }
    }
}
