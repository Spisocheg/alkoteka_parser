# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import re

from itemadapter import ItemAdapter
from pydantic import ValidationError

from .models import AlkotekaModel


class AlkotekaPipeline:
    def process_item(self, item, spider):
        return item


class FormatingFieldsPipeline:
    """Форматирование значений указанных полей item в соответствии с требуемыми условиями"""

    def process_item(self, item, spider):
        if spider.name == 'products_by_category':
            # Например:
            # 1. проверка 'no_image' in item['assets']['main_image'] -> item['assets']['main_image'] = None
            # 2. item['metadata']['stores_list'][i]['quantity'] = int(`quantity`.replace('шт', '').strip())

            # Преобразование title товара по формату "{Название}, {Цвет или Объем}"
            litres_pattern = r'\d[.,]\d{1,2}\s*[лЛ]|\d[лЛ]'
            if not re.search(litres_pattern, item["title"]):                    
                litres = re.findall(litres_pattern, ';'.join(item["section"]))
                try:
                    item["title"] = f'{item["title"]}, {litres[0]}'
                except IndexError:
                    pass

            # Преобразование строкового представления числа скидки в формат "Скидка {discount_percentage}%"
            if item['price_data'].get('sale_tag', None):
                item['price_data']['sale_tag'] = f"Скидка {item['price_data']['sale_tag']}%"
            return item
        else:
            return item


class ValidateFieldsPipeline:
    """Валидация типов данных для указанных полей item (производится посредством моделей Pydantic (файл models.py)).

    Дополнительно: если поле в item равно None, а модель ожидает непустой примитив
    (int/float/str/list/dict/bool), то перед валидацией подставляются безопасные
    значения по умолчанию (0, 0.0, '', [], {}, False). Подробнее в файле models.py
    """

    def process_item(self, item, spider):
        if spider.name == 'products_by_category':
            # Преобразование scrapy.Item в словарь для валидации Pydantic
            item_dict = dict(item)

            try:
                # Создание валидированной модели Pydantic из словаря item_dict
                validated = AlkotekaModel.model_validate(
                    item_dict,
                    from_attributes=False
                )

                # Обновление item валидированными значениями
                for field, value in validated.model_dump().items():
                    item[field] = value

                # При успешной валидации возвращается обновленный item
                spider.logger.info(f"Валидация успешно пройдена для item={item['RPC']}")
                return item

            except ValidationError as e:
                spider.logger.error(
                    f"Validation failed: {e}\n"
                    f"Details: {e.json()}"
                )
                raise

        # Обработка item от других пауков
        else:
            return item


class RenameFieldsPipeline:
    """
    Переименование полей item в соответствии с требованиями выходных данных
    (шаблон переименования settings.py RENAME_PATTERN)
    """

    def process_item(self, item, spider):
        # Получение паттерна переименования для текущего паука из settings
        rename_pattern = spider.settings.get('RENAME_PATTERN', {})
        rename_map = rename_pattern.get(spider.name, {})
        
        if not rename_map:
            return item

        # Преобразование scrapy.Item в словарь
        item_dict = dict(item)

        for field, rename_rule in rename_map.items():            
            # Простое переименование на верхнем уровне
            if isinstance(rename_rule, str):
                if field in item_dict:
                    item_dict[rename_rule] = item_dict.pop(field)
                    spider.logger.info(f"Переименовано: {field} -> {rename_rule}")
            
            # Вложенное переименование
            elif isinstance(rename_rule, dict):
                nested_item = item_dict.get(field)
                
                if nested_item and isinstance(nested_item, dict):
                    # Переименование внутри вложенного объекта
                    for old_name, new_name in rename_rule.items():
                        if old_name in nested_item:
                            nested_item[new_name] = nested_item.pop(old_name)
                            spider.logger.info(f"Переименовано: {field}.{old_name} -> {field}.{new_name}")
                    
                    # Обновление вложенного объекта
                    item_dict[field] = nested_item

        # Возврат словаря, тк scrapy.Item выдаст ошибку из-за новых полей
        return item_dict
