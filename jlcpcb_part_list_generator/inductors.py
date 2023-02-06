from decimal import Decimal
from typing import List

from pint import UnitRegistry

from jlcpcb_part_list_generator.search_model import LIBRARY_TYPES, SearchModel

BASE_VALUES = [
    "1",
    "1.1",
    "1.2",
    "1.3",
    "1.5",
    "1.6",
    "1.8",
    "2",
    "2.2",
    "2.4",
    "2.7",
    "3",
    "3.3",
    "3.6",
    "3.9",
    "4.3",
    "4.7",
    "5.1",
    "5.6",
    "6.2",
    "6.8",
    "7.5",
    "8.2",
    "8.7",
    "9.1",
]

MULTIPLIERS = [
    "1",
    "10",
    "100",
    "1000",
]

UNITS = [
    "nH",
    "uH",
]

COMPONENT_TYPES = [
    "Inductors (SMD)",
    "Power Inductors",
]


def generate_keywords() -> List[str]:
    keywords: List[str] = []

    for value in BASE_VALUES:
        for unit in UNITS:
            for multiplier in MULTIPLIERS:
                d = Decimal(value) * Decimal(multiplier)
                d = d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()

                keywords.append(f"{d}{unit}")

    return keywords


STANDARD_VALUES = generate_keywords()


def generate_search_models() -> List[SearchModel]:
    models: List[SearchModel] = []

    ureg = UnitRegistry(non_int_type=Decimal)
    base_unit = ureg.Unit("uH")

    for value in STANDARD_VALUES:
        for component_type in COMPONENT_TYPES:
            for library_type in LIBRARY_TYPES:
                models.append(
                    SearchModel(
                        firstSortName="Inductors/Coils/Transformers",
                        secondSortName=component_type,
                        componentLibraryType=library_type,
                        keyword=value,
                        base_unit=base_unit,
                    )
                )

    return models
