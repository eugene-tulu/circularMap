from pydantic import BaseModel, Field
from typing import Optional


class MsmeBase(BaseModel):
    enterprise_name: str
    county: str
    sub_county: str
    ward: str
    value_chain: str
    ownership_category: str
    employees: int = Field(ge=1)
    registration_status: str
    year_established: int = Field(ge=1990, le=2030)
    capacity_score: int = Field(ge=1, le=5)
    support_need: str
    latitude: float
    longitude: float


class MsmeCreate(MsmeBase):
    pass


class MsmeUpdate(MsmeBase):
    pass


class Msme(MsmeBase):
    enterprise_id: int
