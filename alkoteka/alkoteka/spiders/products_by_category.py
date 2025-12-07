from collections.abc import AsyncIterator
from typing import Any, Iterable
import json
import math
import re

import scrapy
from scrapy.http import Response
from scrapy.exceptions import CloseSpider
from scrapy.utils.project import get_project_settings

from ..loaders.products_by_category_loaders import (
    AlkotekaLoader, MetadataPBCLoader, AssetsLoader, StockLoader, PriceDataLoader
)


class ProductsByCategorySpider(scrapy.Spider):
    name = "products_by_category"
    allowed_domains = ["alkoteka.com"]
    
    # Переменные, используемые в работе паука
    # city_url          - для получения списка городов
    # cities            - словарь: Название_города=UUID_города
    # city_name         - название города, для которого будет собираться информация
    #                     (используется для получения city_uuid из cities)
    # city_uuid         - uuid города, для которого будет собираться информация
    # per_page          - количество продуктов на странице
    # product_url       - для получения продуктов по категориям + для получения детальной информации о продукте
    # urls_from_file    - список ссылок на категории, которые будут прочитаны из файла и использованы для сбора данных
    #                     (будет забран slug из ссылок)
    # referer_url       - изначальная ссылка для подмены заголовка Referer

    def __init__(self, city=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Установка настроек из settings.py
        self.settings = get_project_settings()
        # Установка настроек парсинга для текущего паука
        self.parsing_params = self.settings.get('PARSING_PARAMS', {}).get(self.name, None)
        if self.parsing_params is None:
            msg = f'Для текущего паука не установлены требуемые параметры сбора'
            raise CloseSpider(msg)

        # Установка названия города
        if city:
            self.city_name = city
        else:
            self.city_name = self.parsing_params.get('DEFAULT_CITY_NAME', 'Краснодар')

        # Установка ссылки на список городов
        self.city_url = self.parsing_params.get('CITY_URL', None)
        # Установка ссылки на страницу списка товаров
        self.product_url = self.parsing_params.get('PRODUCT_URL', None)
        # Установка per_page
        self.per_page = self.parsing_params.get('PER_PAGE', 20)
        # Установка referer
        self.referer_url = self.parsing_params.get('REFERER_URL', None)

        # Сбор невозможен, если хотя бы одна из ссылок не заполнена
        if (self.city_url is None) or (self.product_url is None) or not (self.city_url and self.product_url):
            msg = f'В файле settings.py проекта в словаре настройки паука не заполнены CITY_URL и/или PRODUCT_URL'
            raise CloseSpider(msg)

        # Создание переменной uuid города
        self.city_uuid = ''
        # Создание словаря городов: Название_города=UUID_города
        self.cities = {}
        # Создание списка ссылок на категории
        self.urls_from_file = []

        # Чтение файла links.txt и перенос их в urls_from_file
        # + проверка существования файла, чтение, проверка валидности ссылок, добавление в список urls_from_file
        urls_file = self.settings.get('PROJECT_DIR_PATH') / self.settings.get('URLS_FILENAME')
        if urls_file.exists():
            url_pattern = re.compile(r'^https://alkoteka\.com/catalog/[a-zA-Z0-9\-_]+$')
            with open(urls_file, 'r', encoding='utf-8') as f:
                count = 0
                for line in f:
                    count += 1
                    if line.strip() and url_pattern.match(line.strip()):
                        self.urls_from_file.append(line.strip())

                if len(self.urls_from_file) != count:
                    msg = f'Не все ссылки в файле {urls_file} валидны. Часть из них была проигнорирована'
                    self.logger.warning(msg)

            if not self.urls_from_file:
                msg = f'В файле {urls_file} нет валидных ссылок'
                raise CloseSpider(msg)
        else:
            msg = f'Нет ссылок для сбора данных в файле {urls_file}'
            raise CloseSpider(msg)

    async def start(self) -> AsyncIterator[Any]:
        yield scrapy.Request(url=self.city_url, callback=self.parse_cities,
                             headers={'Referer': self.referer_url + '/'})

    def parse_cities(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()

        # Заполнение словаря: Название_города=UUID_города
        for city in data["results"]:
            self.cities[city["name"].lower()] = city["uuid"]

        # Пагинация списка городов
        if data["meta"]["has_more_pages"]:
            url = f'{self.city_url}&page={data["meta"]["current_page"]+1}'
            yield scrapy.Request(url, callback=self.parse_cities,
                                 headers={'Referer': self.referer_url + '/'})
        else:
            # Установка city_uuid для последующего сбора
            self.set_city_uuid()

            # Создание генераторов каждой категории
            for url in self.urls_from_file:
                root_category_slug = url.split("/")[-1]
                query_params = [
                    f'city_uuid={self.city_uuid}',
                    f'page=1',
                    f'per_page={self.per_page}',
                    f'root_category_slug={root_category_slug}'
                ]
                category_url = f'{self.product_url}?{"&".join(query_params)}'
                referer_url = f'{self.referer_url}/catalog/{root_category_slug}'
                yield scrapy.Request(url=category_url, callback=self.parse,
                                     headers={'Referer': referer_url})

    def calc_similarity(self, s1: str, s2: str) -> float | int:
        """Функция нахождения коэффициента схожести по формуле Жаккара (Jaccard index)"""

        set1 = set(s1.lower())
        set2 = set(s2.lower())
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union != 0 else 0

    def set_city_uuid(self):
        if self.city_name.lower() in self.cities:
            self.city_uuid = self.cities[self.city_name.lower()]
            return

        # Составление списка схожести: (коэфф_схожести, {Название_города=UUID_города})
        similarities = []
        for valid_city in self.cities:
            similarities.append((
                self.calc_similarity(self.city_name.lower(), valid_city),
                valid_city
            ))
        similarities.sort(reverse=True)
        # Выборка 3 наиболее схожих городов
        best_matches = [city for sim, city in similarities[:3]]

        # Подсказка "Возможно вы имели в виду"
        msg = (f"Не найден: '{self.city_name}'. Возможно вы имели в виду один из этих городов: "
               f"{', '.join(list(map(lambda x: x.capitalize(), best_matches)))} ?")
        raise CloseSpider(msg)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        products = response.json()

        # Сбор данных о продуктах на странице списка товаров
        for product in products["results"]:
            main_loader = AlkotekaLoader()
            main_loader.add_value('timestamp', 0)
            main_loader.add_value('RPC', product['vendor_code'])
            main_loader.add_value('url', product['product_url'])
            main_loader.add_value('title', product['name'])
            main_loader.add_value('marketing_tags',
                                  [product["action_labels"][i]['title'] for i in range(len(product["action_labels"]))])

            # Переход на страницу о продукте и продолжение сбора
            root_category_slug = response.url.split('root_category_slug=')[-1]
            product_slug = product["product_url"].split("/")[-1]
            product_url = \
                f'{self.product_url}/{product_slug}?city_uuid={self.city_uuid}'
            referer_url = f'{self.referer_url}/product/{root_category_slug}/{product_slug}'
            yield scrapy.Request(url=product_url, callback=self.parse_product_details,
                                 meta={'loader': main_loader},
                                 headers={'Referer': referer_url})

        # Пагинация по страницам
        root_category_slug = response.url.split("root_category_slug=")[-1]
        query_params = [
            f'city_uuid={self.city_uuid}',
            f'page={products["meta"]["current_page"] + 1}',
            f'per_page={self.per_page}',
            f'root_category_slug={root_category_slug}'
        ]
        if products["meta"]["has_more_pages"]:
            next_page_url = f'{self.product_url}?{"&".join(query_params)}'
            referer_url = f'{self.referer_url}/catalog/{root_category_slug}'
            yield scrapy.Request(url=next_page_url, callback=self.parse,
                                 headers={'Referer': referer_url})

    def parse_product_details(self, response: Response, **kwargs: Any) -> Any:
        data = response.json().get('results')

        main_loader = response.meta['loader']

        brand: str | None = None
        for desc in data["description_blocks"]:
            if desc["code"].lower() == 'brend':
                brand = ';'.join([desc["values"][i]["name"] for i in range(len(desc["values"]))])
                break
        main_loader.add_value('brand', brand)

        section: list = [data["category"]["parent"]["name"]]
        for flabel in data["filter_labels"]:
            section.append(flabel["title"])
        main_loader.add_value('section', section)

        main_loader.add_value('price_data', self.get_product_price_data(data))
        main_loader.add_value('stock', self.get_product_stock(data))
        main_loader.add_value('assets', self.get_product_assets(data))
        main_loader.add_value('metadata', self.get_product_metadata(data))

        main_loader.add_value('variants', 0)

        item = main_loader.load_item()
        if item is None:
            self.logger.warning('AlkotekaLoader.load_item() returned None for %s', response.url)
            return

        yield item

    def get_product_price_data(self, data_result, **kwargs: Any) -> Any:
        price_data = PriceDataLoader()

        price = data_result["price"]
        price_data.add_value('current', price)

        prev_price = data_result["prev_price"]
        price_data.add_value('original', prev_price)

        if price and prev_price:
            sale = str(100 - math.floor(price * 100 / prev_price))
        else:
            # None потому что зачастую - проблема БЕ, что он отдает не все данные
            sale = None
        price_data.add_value('sale_tag', sale)

        return price_data.load_item()

    def get_product_stock(self, data_result, **kwargs: Any) -> Any:
        stock = StockLoader()

        quantity = data_result["quantity_total"]
        stock.add_value('in_stock', False if quantity == 0 else True)
        stock.add_value('count', quantity)

        return stock.load_item()

    def get_product_assets(self, data_result, **kwargs: Any) -> Any:
        assets = AssetsLoader()

        assets.add_value('main_image', data_result["image_url"])

        return assets.load_item()

    def get_product_metadata(self, data_result, **kwargs: Any) -> Any:
        metadata = MetadataPBCLoader()

        description = None
        if data_result["text_blocks"]:
            for desc in data_result["text_blocks"]:
                if desc["title"].lower() == 'описание':
                    description = desc["content"]
        metadata.add_value('description', description)

        metadata.add_value('vendor_code', data_result["vendor_code"])

        gift_package = False

        for block in data_result["description_blocks"]:
            match block["code"].lower():
                case 'cvet':
                    cvet = [block["values"][i]["name"] for i in range(len(block["values"]))]
                    metadata.add_value('color', cvet) # мб список

                case 'obem':
                    obem = {
                        'min': block["min"],
                        'max': block["max"],
                        'unit': block["unit"]
                    }
                    metadata.add_value('litres', obem)  # мб нужна будет в пайплайне обработка ('1 л.' или 1)

                case 'ves':
                    ves = {
                        'min': block["min"],
                        'max': block["max"],
                        'unit': block["unit"]
                    }
                    metadata.add_value('weight', ves)   # мб нужна будет в пайплайне обработка ('1 г' или 1)

                case 'strana':
                    strana = [block["values"][i]["name"] for i in range(len(block["values"]))]
                    metadata.add_value('country', strana)

                case 'region': # список
                    region = [block["values"][i]["name"] for i in range(len(block["values"]))]
                    metadata.add_value('region', region)

                case 'krepost':
                    krepost = {
                        'min': block["min"],
                        'max': block["max"],
                        'unit': block["unit"]
                    }
                    metadata.add_value('strength', krepost)  # мб нужна будет в пайплайне обработка

                case 'vid':
                    vid = [block["values"][i]["name"] for i in range(len(block["values"]))]
                    metadata.add_value('type_', vid)

                case 'proizvoditel':
                    proizvoditel = [block["values"][i]["name"] for i in range(len(block["values"]))]
                    metadata.add_value('manufacturer', proizvoditel)

                case 'soderzanie-saxara':
                    sugar = [block["values"][i]["name"] for i in range(len(block["values"]))]
                    metadata.add_value('sugar', sugar)

                case 'temperatura-podaci':
                    serving_temp = {
                        'values': [str(block["values"][i]["name"]) for i in range(len(block["values"]))],
                        'unit': block["unit"]
                    }
                    metadata.add_value('serving_temp', serving_temp)

                case 'sortovoi-sostav': # список
                    sort_ = [block["values"][i]["name"] for i in range(len(block["values"]))]
                    metadata.add_value('sort_', sort_)

                case 'prodolzitelnost-vyderzki':
                    exposure_time = [block["values"][i]["name"] for i in range(len(block["values"]))]
                    metadata.add_value('exposure_time', exposure_time) # мб нужна будет в пайплайне обработка

                case 'emkost-vyderzki': # список
                    exposure_container = [block["values"][i]["name"] for i in range(len(block["values"]))]
                    metadata.add_value('exposure_container', exposure_container)

                case 'filtration':
                    filtration = [block["values"][i]["name"] for i in range(len(block["values"]))]
                    metadata.add_value('filtration', filtration) # мб список?

                case 'vid-upakovki':
                    type_container = [block["values"][i]["name"] for i in range(len(block["values"]))]
                    metadata.add_value('type_container', type_container) # мб список?

                case 'podarocnaya-upakovka':
                    gift_package = True

        metadata.add_value('gift_package', gift_package)

        metadata.add_value('subname', data_result["subname"])

        stores: list[dict] = []
        for store in data_result["availability"]["stores"]:
            st = {
                'address': store["title"],
                'phone': store["phone"],
                'opening_hours': store["opening_hours"],
                'longitude': store["longitude"],
                'latitude': store["latitude"],
                'price': store["price"],
                'quantity': store["quantity"]
            }
            stores.append(st)
        metadata.add_value('stores_list', stores)

        gastronomics: list[str] = []
        if data_result["gastronomics"]:
            for v in data_result["gastronomics"].values():
                for g in v:
                    gastronomics.append(g["title"])
        metadata.add_value('gastronomics', gastronomics)

        return metadata.load_item()
