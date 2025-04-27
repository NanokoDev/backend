from enum import Enum


class Permission(Enum):
    """An enum for auth & identity"""

    STUDENT = 0
    TEACHER = 1
    ADMIN = 2


class Performance(Enum):
    """A standard to represent the performance of students"""

    NOT_STARTED = 0
    ATTEMPTED = 1
    FAMILIAR = 2
    PROFICIENT = 3
    MASTERED = 4
