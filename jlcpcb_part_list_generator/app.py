import csv
import re
from decimal import Decimal
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional

import click
import requests
from pint import Quantity, UnitRegistry
from pydantic import AnyHttpUrl, BaseModel

import jlcpcb_part_list_generator.capacitors
import jlcpcb_part_list_generator.inductors
import jlcpcb_part_list_generator.resistors
from jlcpcb_part_list_generator.search_model import SearchModel

SEARCH_URL = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"


class RequestModel(BaseModel):
    currentPage: int
    pageSize: int
    keyword: str
    firstSortName: str
    secondSortName: str
    searchSource: str
    componentAttributes: List[Any]
    stockFlag: bool
    componentLibraryType: str
    stockSort: bool


class ComponentPrice(BaseModel):
    endNumber: int
    productPrice: float
    startNumber: int


class ListItem(BaseModel):
    canPresaleNumber: int
    componentBrandEn: str
    componentCode: str
    componentId: int
    componentImageUrl: Optional[str]
    componentLibraryType: str
    componentModelEn: str
    componentName: str
    componentPrices: List[ComponentPrice]
    componentProductType: int
    componentSource: str
    componentSpecificationEn: str
    componentTypeEn: str
    dataManualUrl: Optional[str]
    describe: str
    erpComponentName: str
    firstSortAccessId: str
    lcscGoodsUrl: Optional[str]
    mergedComponentCode: Any
    minImage: Optional[str]
    secondSortAccessId: Optional[str]
    stockCount: int
    urlSuffix: str


class ComponentPageInfo(BaseModel):
    endRow: int
    hasNextPage: bool
    hasPreviousPage: bool
    isFirstPage: bool
    isLastPage: bool
    list: List[ListItem]
    navigateFirstPage: int
    navigateLastPage: int
    navigatePages: int
    navigatepageNums: Any
    nextPage: int
    pageNum: int
    pageSize: int
    pages: int
    prePage: int
    size: int
    startRow: int
    total: int


class ChildSortListItem(BaseModel):
    childSortList: Any
    componentCount: int
    componentSortKeyId: int
    enDescription: str
    grade: int
    parentId: int
    sortImgUrl: str
    sortName: str
    sortUuid: str


class SortAndCountVoListItem(BaseModel):
    childSortList: List[ChildSortListItem]
    componentCount: int
    componentSortKeyId: int
    enDescription: str
    grade: int
    parentId: int
    sortImgUrl: str
    sortName: str
    sortUuid: str


class Data(BaseModel):
    componentPageInfo: Optional[ComponentPageInfo]
    sortAndCountVoList: Optional[List[SortAndCountVoListItem]]


class ResponseModel(BaseModel):
    code: int
    data: Data
    message: Any


class CSVRow(BaseModel):
    ComponentCode: str
    ComponentModel: str
    ComponentSpecification: str
    StockCount: int
    ERPComponentName: str
    ComponentType: str
    ComponentLibraryType: str
    SortableValueMagnitude: Optional[Decimal]
    SortableValueUnit: Optional[str]
    Datasheet: Optional[AnyHttpUrl]


def get_items(model_generator: Callable[[], List[SearchModel]]) -> Iterator[CSVRow]:
    current_page = 0
    default_model = {
        "pageSize": 25,
        "searchSource": "search",
        "componentAttributes": [],
        "stockFlag": True,
        "stockSort": True,
    }

    ureg = UnitRegistry(non_int_type=Decimal)

    with click.progressbar(
        model_generator(),
        item_show_func=lambda x: str(x),
    ) as search_models:
        for model in search_models:
            val: Quantity = None
            check: Optional[re.Pattern] = None

            if model.base_unit is not None:
                val = ureg.Quantity(model.keyword).to(model.base_unit)

            if model.keyword != "":
                check = re.compile(r"[ ]?" + re.escape(model.keyword) + "(?![\w-])")

            while True:
                current_page += 1
                default_model["currentPage"] = current_page

                data = {}
                data.update(default_model)
                data.update(model.dict())

                req = RequestModel(
                    **data,
                )

                resp = requests.post(SEARCH_URL, json=req.dict())
                resp.raise_for_status()
                resp_model = ResponseModel.parse_raw(resp.content)

                if (
                    resp_model.data.componentPageInfo
                    and resp_model.data.componentPageInfo.pageNum == 1
                ):
                    search_models.item_show_func = (
                        lambda x: f"page {resp_model.data.componentPageInfo.pageNum} / {resp_model.data.componentPageInfo.pages}"
                        if resp_model.data.componentPageInfo
                        else "Done"
                    )
                    if search_models.length is None:
                        search_models.length = 1
                    search_models.length += resp_model.data.componentPageInfo.pages

                search_models.update(1)

                if (
                    not resp_model.data.componentPageInfo
                    or len(resp_model.data.componentPageInfo.list) == 0
                ):
                    break

                for item in resp_model.data.componentPageInfo.list:
                    if check and check.search(item.erpComponentName) is None:
                        print(
                            f"skipping {item.erpComponentName}; doesn't match {model.keyword}"
                        )
                        continue

                    yield CSVRow(
                        ComponentCode=item.componentCode,
                        ComponentModel=item.componentModelEn,
                        ComponentSpecification=item.componentSpecificationEn,
                        StockCount=item.stockCount,
                        ERPComponentName=item.erpComponentName,
                        ComponentType=item.componentTypeEn,
                        ComponentLibraryType=item.componentLibraryType,
                        Datasheet=item.dataManualUrl if item.dataManualUrl else None,
                        SortableValueMagnitude=val.magnitude if val else None,
                        SortableValueUnit=str(val.units) if val else None,
                    )


def write_csv(path: str, items: Iterable[CSVRow]):
    with open(path, "w") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CSVRow.schema()["properties"].keys(),
        )
        writer.writeheader()

        for item in items:
            writer.writerow(item.dict())


def get_basic_parts():
    items = get_items(
        lambda: [
            SearchModel(
                firstSortName="",
                secondSortName="",
                keyword="",
                base_unit=None,
                componentLibraryType="base",
            )
        ]
    )
    write_csv("baseparts.csv", items)


def get_all_expand_parts():
    items = get_items(
        lambda: [
            SearchModel(
                firstSortName="",
                secondSortName="",
                keyword="",
                base_unit=None,
                componentLibraryType="expand",
            )
        ]
    )
    write_csv("expandparts.csv", items)


def get_capacitors():
    items = get_items(jlcpcb_part_list_generator.capacitors.generate_search_models)
    write_csv("capacitors.csv", items)


def get_resistors():
    items = get_items(jlcpcb_part_list_generator.resistors.generate_search_models)
    write_csv("resistors.csv", items)


def get_inductors():
    items = get_items(jlcpcb_part_list_generator.inductors.generate_search_models)
    write_csv("inductors.csv", items)


@click.command()
def get_all():
    print("getting basic parts")
    get_basic_parts()

    print("getting expand parts")
    get_all_expand_parts()

    # print("getting resistors")
    # get_resistors()
    # print("getting capacitors")
    # get_capacitors()
    # print("getting inductors")
    # get_inductors()


if __name__ == "__main__":
    get_all()
