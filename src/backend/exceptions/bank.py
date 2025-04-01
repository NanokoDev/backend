class BankDatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message


class SubQuestionIdInvalid(BankDatabaseError):
    def __init__(self, sub_question_id: int) -> None:
        super().__init__(f"Invalid sub_question_id {sub_question_id}")


class QuestionIdInvalid(BankDatabaseError):
    def __init__(self, question_id: int) -> None:
        super().__init__(f"Invalid question_id {question_id}")


class ImageIdInvalid(BankDatabaseError):
    def __init__(self, image_id: int) -> None:
        super().__init__(f"Invalid image_id {image_id}")
