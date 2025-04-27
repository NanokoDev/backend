class UserDatabaseError(Exception):
    """Base class for all exceptions related to the bank database"""

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message


class UserIdInvalid(UserDatabaseError):
    """Exception raised when a subquestion_id is invalid"""

    def __init__(self, user_id: int) -> None:
        super().__init__(f"Invalid user_id {user_id}")
