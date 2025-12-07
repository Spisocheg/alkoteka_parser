# Парсер alkoteka.com

Этот парсер позволяет собирать информацию об алкогольных товарах с сайта `alcoteka.com`. Поддерживает парсинг по городам, категориям, пагинацию, автоматическую ротацию прокси и браузерную имитацию. Собирает все возможные данные о товаре и записывает их в файл `.json`.

## Требования

- [Python](https://www.python.org/downloads/) >= 3.11.1
- [Scrapy](https://pypi.org/project/Scrapy/) >= 2.13.4
- [Pydantic](https://pypi.org/project/pydantic/) >= 2.12.5
- [scrapy-rotating-proxies](https://pypi.org/project/scrapy-rotating-proxies/) >= 0.6.2
- [browserforge](https://pypi.org/project/browserforge/) >= 1.2.3

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Spisocheg/alkoteka_parser
   ```
2. Перейдите в директорию проекта (если не в ней):
   ```bash
   cd alkoteka_parser
   ```

## Первый запуск

1. Создайте виртуальное окружение. В корне проекта введите следующее:
   ```bash
   ... > python -m venv .venv
   ```
2. После непродолжительной загрузки в корне проекта появится новая папка (с именем `.venv`). Активируйте виртуальное окружение:
   ```bash
   ... > .\.venv\Scripts\activate  # На Windows
   # или
   ... > source .venv/bin/activate  # На Linux/macOS
   ```
3. В начале строки добавится имя виртуального окружения в скобках. Установите требуемые для работы зависимости:
   ```bash
   (.venv) ... > python -m pip install -r .\requirements.txt
   ```
4. После установки пакетов можете перейти к запуску:
   ```bash
   (.venv) ... > scrapy crawl products_by_category -O output.json -a city=Москва
   ```

## Настройки

### Настройка города для парсинга

Город указывается в команде парсинга с помощью ключа `-a`, после которого через пробел указывается строка `city=city_name`, где `city_name` - название города; к регистру не чувствительно. Если введено `city_name`, которое не найдено в списке доступных городов для выбора не сайте, то парсинг не начнется и будт предложены наиболее близкие к введенному варианты. Если значение не введено совсем, то будет использовано название города из переменной `DEFAULT_CITY_NAME` файла `settings.py`. Например:

```bash
(.venv) ... > scrapy crawl products_by_category -O output.json -a city=москва

(.venv) ... > scrapy crawl products_by_category -O output.json -a city=Краснр
...
[scrapy.core.engine] INFO: Spider closed (Не найден: 'Краснр'. Возможно вы имели в виду один из этих городов: Краснодар, Курганинск, Абинск ?)
```

### Настройка имени файла с входными ссылками

Список ссылок для сбора данных подается на вход с помощью файла в формате `.txt`. Имя файла описывается в файле `settings.py` переменной `URLS_FILENAME`. Для указания корневой папки проекта используется переменная `PROJECT_DIR_PATH` в этом же файле и ее можно использовать для указания относительной ссылки на входной файл. Значение переменной `URLS_FILENAME` по умолчанию:

```python
URLS_FILENAME = PROJECT_DIR_PATH / 'links.txt'
```

### Настройка параметров HTTP запроса

Содержится в файле `settings.py` переменной `PARSING_PARAMS`. Поля `PARSING_PARAMS` и значение по умолчанию:
```python
PARSING_PARAMS = {
    # Имя паука (поле name паука)
    'products_by_category': {
        # Количество запрашиваемых товаров на странице категории
        'PER_PAGE': 20,
        # Название города по умолчанию для сбора данных
        'DEFAULT_CITY_NAME': 'Краснодар',
        # URL для сбора списка городов и их uuid
        'CITY_URL': 'https://alkoteka.com/web-api/v1/city?city_uuid=396df2b5-7b2b-11eb-80cd-00155d039009',
        # URL для сбора списка товаров на странице категории, а также информации о товаре
        'PRODUCT_URL': 'https://alkoteka.com/web-api/v1/product',
        # URL для подстановки в заголовок Referer запроса
        'REFERER_URL': 'https://alkoteka.com'
    }
}
```

### Настройка параметра переименования полей Item

Используется для переименования каких-либо полей в выходном файле, если внутри скрипта они имеют иное наименование. Поддерживает только 2 уровня вложенности. Параметры хранятся в файле `settings.py` переменной `RENAME_PATTERN` и используется конвеером `RenameFieldsPipeline`. Формат переменной и значение по умолчанию:

```python
# Формат:
# spider.name : {
#   'old_field_name': 'new_field_name',
#   'parent_field': {
#       'old_field_name': 'new_field_name'
# }
RENAME_PATTERN = {
    # Имя паука (поле name паука)
    'products_by_category': {
        # Поле item, внутри которого содержится вложенная структура (в.с.)
        'metadata': {
            # Текущее название поля в.с. : Новое название поля в.с.
            'description': '__description'
        }
        # Текущее название поля : Новое название поля
        # 'brand': 'trademark'
    }
}
```

### Настройка валидации типов данных полей Item

Валидация осуществляется с помощью библиотеки Pydantic и в конвеере `ValidateFieldsPipeline`. Ожидаемые типы данных описаны в файле `models.py`.

### Настройка форматирования строк

Форматирование строк осуществляется в конвеере `FormatingFieldsPipeline` файла `pipelines.py`.

### Настройка прокси

Ротация прокси происходит с помощью библиотеки `scrapy-rotating-proxies`. В файле `settings.py` приведены не все, но самые полезные для этого проекта параметры этой библиотеки:

```python
# Ссылка на файл с адресами прокси
ROTATING_PROXY_LIST_PATH = PROJECT_DIR_PATH / 'proxies.txt'
# Количество повторов отправки запроса от одного адреса, имеющего статус не `GOOD`
ROTATING_PROXY_PAGE_RETRY_TIMES = 5
# Приостановка работы паука при исчерпывании списка прокси
ROTATING_PROXY_CLOSE_SPIDER = False
```

## Использование

### Запуск

1. Перейдите в папку с проектом. Активируйте виртуальное окружение:
   ```bash
   ... > .\.venv\Scripts\activate  # Windows
   # или
   ... > source .venv/bin/activate  # Linux/macOS
   ```
2. В начале строки добавится имя виртуального окружения в скобках. Запустите парсер:
   ```bash
   (.venv) ... > scrapy crawl products_by_category -a city=сочи -O output.json
   ```

### Результат

После завершения парсинга в папке `./alkoteka` относительно корневой директории проекта появится файл с форматом `.json` и указанным после ключа `-o` (или `-O` для перезаписи выходного файла) названием выходного файла со списком словарей (объектов). Каждый объект содержит информацию о товаре:

```txt
{
  "timestamp": int,
  "RPC": str,
  "url": str,
  "title": str,
  "marketing_tags": list[str],
  "brand": str,
  "section": list[str],
  "price_data": {
    "current": float,
    "original": float,
    "sale_tag": str в формате "Скидка {discount_percentage}%"
  },
  "stock": {
    "in_stock": bool,
    "count": int
  },
  "assets": {
    "main_image": str,
    "set_images": list[str],
    "view360": list[str],
    "video": list[str]
  },
  "metadata": {
    "__description": str,
    "vendor_code": int,
    "color": list[str]
    "litres": {
        "min": float,
        "max": float,
        "unit": str
    }
    "weight": {
        "min": float,
        "max": float,
        "unit": str
    }
    "country": list[str]
    "region": list[str]
    "strength": {
        "min": int,
        "max": int,
        "unit": str
    }
    "type_": list[str]
    "manufacturer": list[str]
    "sugar": list[str]
    "serving_temp": {
        "values": list[str],
        "unit": str
    }
    "sort_": list[str]
    "exposure_time": list[str]
    "exposure_container": list[str]
    "filtration": list[str]
    "type_container": list[str]
    "gift_package": bool
    "subname": str
    "stores_list": list[dict]
    "gastronomics": list[str]
  },
  "variants": int
}
```

### Параметры командной строки

Командная строка принимает следующие ключи после основной команды `scrapy crawl <spider_name>`:

- `-O <output_file>` - перезаписать выходной файл (обязательно, если не указан `-o`)
- `-o <output_file>` - добавить результаты в существующий файл или создать новый (обязательно, если не указан `-O`)
- `-a city=<city>` - город для парсинга (опционально)

## Возможности

- [x] Парсинг товаров по категориям из входного файла
- [x] Обход пагинации и страниц о товаре
- [x] Поддержка выбора города (с выбором при неправильном вводе)
- [x] Составление списка городов в начале каждого парсинга (гарантия актуальности)
- [x] Автоматическая ротация прокси-серверов
- [x] Браузерная имитация через BrowserForge
- [x] Динамический Referer для имитации навигации
- [x] Многоуровневая обработка данных через ItemLoaders
- [x] Форматирование выходных данных (скидки, названия товаров)
- [x] Валидация выходных данных через Pydantic моделей
- [x] Гарантия наличия всех полей при экспорте в JSON
- [x] Переименование полей вывода при надобности (простые и вложенные)
- [x] Обработка невалидных response до их поступления в паука
- [x] Гибкая настройка паука и парсера в целом
- [x] Архитектура парсера, поддерживающая масштабируемость за счет новых пауков

## Структура проекта

```
alkoteka_parser/                                # Корень проекта
├── alkoteka/
│   ├── alkoteka/
│   │   ├── loaders/                            # Пользовательские ItemLoaders
│   │   │   ├── __init__.py
│   │   │   └── products_by_category_loaders.py # ItemLoaders для паука products_by_category
│   │   ├── spiders/                            # Пауки
│   │   │   ├── __init__.py
│   │   │   └── products_by_category.py         # Описание логики работы паука products_by_category
│   │   ├── __init__.py
│   │   ├── items.py                            # Описание Items (структуры хранения данных)
│   │   ├── middlewares.py                      # Пользовательские Middlewares (spider / downloader промежуточное ПО)
│   │   ├── models.py                           # Pydantic схемы валидации
│   │   ├── pipelines.py                        # Пользовательские Pipelines (конвееры обработки данных)
│   │   └── settings.py                         # Настройки парсера и проекта
│   └── scrapy.cfg                              # Конфигурация Scrapy
├── links.txt                                   # Входной файл с ссылками на категории
├── proxies.txt                                 # Файл с адресами прокси серверов
├── README.md                                   # Описание проекта
└── requirements.txt                            # Зависимости проекта
```

---

Если есть вопросы, пишите: https://t.me/Spisocheg
