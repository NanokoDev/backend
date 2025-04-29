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


class UserEmailInvalid(UserDatabaseError):
    """Exception raised when a user email is invalid"""

    def __init__(self, email: str) -> None:
        super().__init__(f"Invalid email {email}")


class ClassIdInvalid(UserDatabaseError):
    """Exception raised when a class_id is invalid"""

    def __init__(self, class_id: int) -> None:
        super().__init__(f"Invalid class_id {class_id}")


class AssignmentIdInvalid(UserDatabaseError):
    """Exception raised when an assignment_id is invalid"""

    def __init__(self, assignment_id: int) -> None:
        super().__init__(f"Invalid assignment_id {assignment_id}")


class UserEmailAlreadyExists(UserDatabaseError):
    """Exception raised when a user email already exists"""

    def __init__(self, email: str) -> None:
        super().__init__(f"Email {email} already exists")


class UsernameAlreadyExists(UserDatabaseError):
    """Exception raised when a username already exists"""

    def __init__(self, username: str) -> None:
        super().__init__(f"Username {username} already exists")


class ClassAlreadyExists(UserDatabaseError):
    """Exception raised when a class already exists"""

    def __init__(self, class_name: str) -> None:
        super().__init__(f"Class {class_name} already exists")


class ClassEnterCodeIncorrect(UserDatabaseError):
    """Exception raised when a class enter code is incorrect"""

    def __init__(self, enter_code: str) -> None:
        super().__init__(f"Incorrect enter code {enter_code}")
