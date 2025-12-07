# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from os import scandir

import scrapy


class PriceDataNestedItem(scrapy.Item):
    current = scrapy.Field()            # price
    original = scrapy.Field()           # "Цена в магазине без оформления резерва"
    sale_tag = scrapy.Field()           # "Скидка {discount_percentage}%" |красным цветом|


class StockNestedItem(scrapy.Item):
    in_stock = scrapy.Field()           # quantity_total != 0
    count = scrapy.Field()              # quantity_total в json


class AssetsNestedItem(scrapy.Item):
    main_image = scrapy.Field()         # есть
    set_images = scrapy.Field()         # нет
    view360 = scrapy.Field()            # нет
    video = scrapy.Field()              # нет


class MetadataNestedItem(scrapy.Item):
    description = scrapy.Field()        # описание |переименование в __description в пайплайне|


class AlkotekaItem(scrapy.Item):
    timestamp = scrapy.Field()          # Дата и время сбора товара в формате timestamp
    RPC = scrapy.Field()                # артикул
    url = scrapy.Field()                # follow ссылка на товар |response.url|
    title = scrapy.Field()              # название
    marketing_tags = scrapy.Field()     # плашки слева снизу на карточке товара |"СКИДКА", "ДО -10% ОНЛАЙН", "НОВИНКА"|
    brand = scrapy.Field()              # бренд
    section = scrapy.Field()            # / breadcrumbs / + плашки овальные
    price_data = scrapy.Field()     # NESTED
    stock = scrapy.Field()          # NESTED
    assets = scrapy.Field()         # NESTED
    metadata = scrapy.Field()       # NESTED
    variants = scrapy.Field()


class MetadataPBCNestedItem(MetadataNestedItem):
    """metadata для паука ProductsByCategorySpider"""

    vendor_code = scrapy.Field()        # артикул
    color = scrapy.Field()              # цвет
    litres = scrapy.Field()             # объем [в литрах]
    weight = scrapy.Field()             # вес [в граммах]
    country = scrapy.Field()            # страна
    region = scrapy.Field()             # регион (список)
    strength = scrapy.Field()           # крепость [в процентах]
    type_ = scrapy.Field()              # вид
    manufacturer = scrapy.Field()       # производитель
    sugar = scrapy.Field()              # содержание сахара
    serving_temp = scrapy.Field()       # температура подачи
    sort_ = scrapy.Field()              # сортовой состав (список)
    exposure_time = scrapy.Field()      # продолжительность выдержки [в месяцах]
    exposure_container = scrapy.Field() # емкость выдержки (список)
    filtration = scrapy.Field()         # фильтрация
    type_container = scrapy.Field()     # вид упаковки
    gift_package = scrapy.Field()       # подарочная упаковка (bool)
    subname = scrapy.Field()            # оригинальное название |для зарубежного|
    stores_list = scrapy.Field()        # магазины из "Наличие в магазинах" (список)
    gastronomics = scrapy.Field()       # "Гастрономические сочетания" (список)
