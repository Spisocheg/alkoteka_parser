from pydantic import BaseModel, Field, model_validator


class PriceDataModel(BaseModel):
    current: float = 0.0
    original: float = 0.0
    sale_tag: str = Field(default='', pattern=r'^(Скидка [0-9]{1,2}%)?$')


class StockModel(BaseModel):
    in_stock: bool = False
    count: int = 0


class AssetsModel(BaseModel):
    main_image: str = ''
    set_images: list[str] = Field(default_factory=list)
    view360: list[str] = Field(default_factory=list)
    video: list[str] = Field(default_factory=list)


class MetadataModel(BaseModel):
    description: str = ''


class MetadataPBCModel(MetadataModel):
    vendor_code: int = 0
    color: list = Field(default_factory=list)
    litres: dict = Field(default_factory=dict)
    weight: dict = Field(default_factory=dict)
    country: list = Field(default_factory=list)
    region: list = Field(default_factory=list)
    strength: dict = Field(default_factory=dict)
    type_: list = Field(default_factory=list)
    manufacturer: list = Field(default_factory=list)
    sugar: list = Field(default_factory=list)
    serving_temp: dict = Field(default_factory=dict)
    sort_: list = Field(default_factory=list)
    exposure_time: list = Field(default_factory=list)
    exposure_container: list = Field(default_factory=list)
    filtration: list = Field(default_factory=list)
    type_container: list = Field(default_factory=list)
    gift_package: bool = False
    subname: str = ''
    stores_list: list = Field(default_factory=list)
    gastronomics: list = Field(default_factory=list)


class AlkotekaModel(BaseModel):
    timestamp: int
    RPC: str
    url: str
    title: str
    marketing_tags: list[str] = Field(default_factory=list)
    brand: str = ''
    section: list[str] = Field(default_factory=list)
    price_data: PriceDataModel
    stock: StockModel
    assets: AssetsModel
    metadata: MetadataModel | MetadataPBCModel
    variants: int = Field(default=0, ge=0)

    @model_validator(mode='before')
    @classmethod
    def convert_all_nones(cls, values):
        """Глобальный обработчик для всех полей: конвертирует все None в примитивы"""
        type_defaults = {
            'int': 0,
            'float': 0.0,
            'str': '',
            'bool': False,
            'list': [],
            'dict': {},
        }

        # Итерация по сведениям о полях модели
        for field_name, field_info in cls.model_fields.items():
            # Получение по имени поля значения этого поля; если значение этого поля - None
            if values.get(field_name) is None:
                # Получение типа поля из аннотаций модели (предусмотрено в тч если аннотация импортирована из typing)
                field_type = str(field_info.annotation).replace('typing.', '').lower()

                # Установка значений полей в соответствии с указанными примитивами
                if field_type.startswith('int'):
                    values[field_name] = type_defaults['int']
                elif field_type.startswith('float'):
                    values[field_name] = type_defaults['float']
                elif field_type.startswith('str'):
                    values[field_name] = type_defaults['str']
                elif field_type.startswith('bool'):
                    values[field_name] = type_defaults['bool']
                elif field_type.startswith('list'):
                    values[field_name] = type_defaults['list']
                elif field_type.startswith('dict'):
                    values[field_name] = type_defaults['dict']

        return values
