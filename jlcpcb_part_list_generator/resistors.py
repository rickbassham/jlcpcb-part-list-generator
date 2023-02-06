from decimal import Decimal
from typing import List

from pint import UnitRegistry

from jlcpcb_part_list_generator.search_model import LIBRARY_TYPES, SearchModel

RESISTOR_VALUES_1PERCENT = [
    "10.0",
    "10.2",
    "10.5",
    "10.7",
    "11.0",
    "11.3",
    "11.5",
    "11.8",
    "12.1",
    "12.4",
    "12.7",
    "13.0",
    "13.3",
    "13.7",
    "14.0",
    "14.3",
    "14.7",
    "15.0",
    "15.4",
    "15.8",
    "16.2",
    "16.5",
    "16.9",
    "17.4",
    "17.8",
    "18.2",
    "18.7",
    "19.1",
    "19.6",
    "20.0",
    "20.5",
    "21.0",
    "21.5",
    "22.1",
    "22.6",
    "23.2",
    "23.7",
    "24.3",
    "24.9",
    "25.5",
    "26.1",
    "26.7",
    "27.4",
    "28.0",
    "28.7",
    "29.4",
    "30.1",
    "30.9",
    "31.6",
    "32.4",
    "33.2",
    "34.0",
    "34.8",
    "35.7",
    "36.5",
    "37.4",
    "38.3",
    "39.2",
    "40.2",
    "41.2",
    "42.2",
    "43.2",
    "44.2",
    "45.3",
    "46.4",
    "47.5",
    "48.7",
    "49.9",
    "51.1",
    "52.3",
    "53.6",
    "54.9",
    "56.2",
    "57.6",
    "59.0",
    "60.4",
    "61.9",
    "63.4",
    "64.9",
    "66.5",
    "68.1",
    "69.8",
    "71.5",
    "73.2",
    "75.0",
    "76.8",
    "78.7",
    "80.6",
    "82.5",
    "84.5",
    "86.6",
    "88.7",
    "90.9",
    "93.1",
    "95.3",
    "97.6",
]

UNIT = "Ω"

MULTIPLIERS = [
    "0.0001",
    "0.001",
    "0.01",
    "0.1",
    "1",
    "10",
    "100",
    "1000",
    "10000",
    "100000",
    "1000000",
]


def convert_units(unit: str) -> str:
    if unit == "ohm":
        return "Ω"
    elif unit == "kiloohm":
        return "kΩ"
    elif unit == "megaohm":
        return "MΩ"
    elif unit == "gigaohm":
        return "GΩ"
    elif unit == "milliohm":
        return "mΩ"
    elif unit == "microohm":
        return "μΩ"
    elif unit == "nanoohm":
        return "nΩ"
    elif unit == "picoohm":
        return "pΩ"
    elif unit == "femtoohm":
        return "fΩ"
    elif unit == "attoohm":
        return "aΩ"
    elif unit == "zeptoohm":
        return "zΩ"
    elif unit == "yoctoohm":
        return "yΩ"
    else:
        raise ValueError("Unknown unit: " + unit)


def generate_keywords() -> List[str]:
    ureg = UnitRegistry(non_int_type=Decimal)

    keywords = []
    for val in RESISTOR_VALUES_1PERCENT:
        for mult in MULTIPLIERS:
            reduced = (
                (ureg.ohm * Decimal(val) * Decimal(mult))
                .to_reduced_units()
                .to_compact()
            )

            d = Decimal(reduced.magnitude)

            d = d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()

            keyword = str(d) + convert_units(str(reduced.units))

            keywords.append(keyword)

    return keywords


STANDARD_VALUES = generate_keywords()
COMPONENT_TYPES = [
    "Chip Resistor - Surface Mount",
]


def generate_search_models() -> List[SearchModel]:
    models: List[SearchModel] = []

    ureg = UnitRegistry(non_int_type=Decimal)
    base_unit = ureg.Unit("ohm")

    for value in STANDARD_VALUES:
        for component_type in COMPONENT_TYPES:
            for library_type in LIBRARY_TYPES:
                models.append(
                    SearchModel(
                        firstSortName="Resistors",
                        secondSortName=component_type,
                        componentLibraryType=library_type,
                        keyword=value,
                        base_unit=base_unit,
                    )
                )

    return models
