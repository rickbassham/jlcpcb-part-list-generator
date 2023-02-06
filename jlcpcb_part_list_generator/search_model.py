from typing import Optional

from pint import Unit
from pydantic import BaseModel

LIBRARY_TYPES = ["", "base"]


class SearchModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    firstSortName: str
    secondSortName: str
    componentLibraryType: str
    keyword: str
    base_unit: Optional[Unit]

    def __str__(self):
        return f"{self.keyword} {self.secondSortName} {self.componentLibraryType}"
