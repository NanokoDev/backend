from enum import Enum


class Permission(Enum):
    """An enum for auth & identity"""

    STUDENT = 0
    TEACHER = 1
    ADMIN = 2

    def __lt__(self, other: "Permission"):
        return self.value < other.value

    def __le__(self, other: "Permission"):
        return self.value <= other.value

    def __gt__(self, other: "Permission"):
        return self.value > other.value

    def __ge__(self, other: "Permission"):
        return self.value >= other.value


class Performance(Enum):
    """A standard to represent the performance of students"""

    NOT_STARTED = 0
    ATTEMPTED = 1
    FAMILIAR = 2
    PROFICIENT = 3
    MASTERED = 4
