import datetime
from typing import List
from enum import IntEnum
from pydantic import BaseModel, Field


class Trend(IntEnum):
    """Trend used to indicate student performance trend over time."""

    DECEASING_STRONG = -2
    DECEASING_SLIGHT = -1
    STABLE = 0
    INCREASING_SLIGHT = 1
    INCREASING_STRONG = 2


class ProcessPerformances(BaseModel):
    """Performance of a student in process ideas."""

    formulate: float = Field(0, ge=0, le=4)
    apply: float = Field(0, ge=0, le=4)
    explain: float = Field(0, ge=0, le=4)


class Performances(BaseModel):
    """Performance of a student in all content ideas."""

    operations_on_numbers: ProcessPerformances
    mathematical_relationships: ProcessPerformances
    spatial_properties_and_representations: ProcessPerformances
    location_and_navigation: ProcessPerformances
    measurement: ProcessPerformances
    statistics_and_data: ProcessPerformances
    elements_of_chance: ProcessPerformances


class ProcessTrends(BaseModel):
    """Trend of a student in process ideas."""

    formulate: Trend
    apply: Trend
    explain: Trend


class PerformanceTrends(BaseModel):
    """Trend of a student in all content ideas."""

    operations_on_numbers: ProcessTrends
    mathematical_relationships: ProcessTrends
    spatial_properties_and_representations: ProcessTrends
    location_and_navigation: ProcessTrends
    measurement: ProcessTrends
    statistics_and_data: ProcessTrends
    elements_of_chance: ProcessTrends


class ProcessData(BaseModel):
    """Arrays of performances of a student in process ideas."""

    formulate: List[int] = Field(default_factory=list)
    apply: List[int] = Field(default_factory=list)
    explain: List[int] = Field(default_factory=list)


class PerformancesData(BaseModel):
    """Arrays of performances of a student in all content ideas."""

    operations_on_numbers: ProcessData
    mathematical_relationships: ProcessData
    spatial_properties_and_representations: ProcessData
    location_and_navigation: ProcessData
    measurement: ProcessData
    statistics_and_data: ProcessData
    elements_of_chance: ProcessData


class PerformanceDateData(BaseModel):
    """Performance data of a student over time."""

    performances: List[float]
    dates: List[datetime.datetime]
