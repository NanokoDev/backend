from enum import IntEnum


class ProcessType(IntEnum):
    """Process enum for the process of subquestions"""

    FORMULATE = 0
    APPLY = 1
    EXPLAIN = 2


class ConceptType(IntEnum):
    """Concept enum for the concept of subquestions"""

    OPERATIONS_ON_NUMBERS = 0
    MATHEMATICAL_RELATIONSHIPS = 1
    SPATIAL_PROPERTIES_AND_REPRESENTATIONS = 2
    LOCATION_AND_NAVIGATION = 3
    MEASUREMENT = 4
    STATISTICS_AND_DATA = 5
    ELEMENTS_OF_CHANCE = 6
