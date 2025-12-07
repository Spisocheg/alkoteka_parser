import time
from typing import Any

from itemloaders import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Identity

from ..items import (
    AlkotekaItem, AssetsNestedItem, StockNestedItem, PriceDataNestedItem, MetadataNestedItem, MetadataPBCNestedItem
)


class PriceDataLoader(ItemLoader):
    default_item_class = PriceDataNestedItem
    default_output_processor = TakeFirst()

    current_in = MapCompose(float)
    original_in = MapCompose(float)
    sale_tag_in = MapCompose(str.strip)


class StockLoader(ItemLoader):
    default_item_class = StockNestedItem
    default_output_processor = TakeFirst()

    in_stock_in = MapCompose(bool)
    count_in = MapCompose(int)


class AssetsLoader(ItemLoader):
    default_item_class = AssetsNestedItem
    default_output_processor = Identity()
    default_input_processor = Identity()

    main_image_in = MapCompose(str.strip)
    main_image_out = TakeFirst()


class MetadataLoader(ItemLoader):
    default_item_class = MetadataNestedItem
    default_output_processor = Identity()
    default_input_processor = Identity()

    description_in = MapCompose(str.strip)
    description_out = TakeFirst()

class AlkotekaLoader(ItemLoader):
    default_item_class = AlkotekaItem
    default_output_processor = TakeFirst()
    default_input_processor = MapCompose(str.strip)

    timestamp_in = MapCompose(lambda x: int(time.time()))
    RPC_in = MapCompose(str)
    marketing_tags_in = Identity()
    marketing_tags_out = Identity()
    section_in = Identity()
    section_out = Identity()
    price_data_in = Identity()
    stock_in = Identity()
    assets_in = Identity()
    metadata_in = Identity()
    variants_in = Identity()


class MetadataPBCLoader(MetadataLoader):
    default_item_class = MetadataPBCNestedItem

    vendor_code_in = MapCompose(int)
    vendor_code_out = TakeFirst()
    litres_out = TakeFirst()
    weight_out = TakeFirst()
    strength_out = TakeFirst()
    serving_temp_out = TakeFirst()
    gift_package_in = MapCompose(bool)
    gift_package_out = TakeFirst()
    subname_in = MapCompose(str.strip)
    subname_out = TakeFirst()
