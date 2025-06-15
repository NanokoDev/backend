import pytz
import datetime
import numpy as np
from typing import Dict, Optional, List

from backend.db.user import UserManager
from backend.exceptions.user import ClassIdInvalid
from backend.db.models.user import CompletedSubQuestion
from backend.types.question import ConceptType, ProcessType
from backend.services.analyzer.models import (
    Trend,
    Performances,
    PerformancesData,
    PerformanceTrends,
    PerformanceDateData,
)


class Analyzer:
    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager

    async def get_best_performances(
        self,
        user_id: int,
    ) -> Performances:
        """Get the best performances of a user.

        Args:
            user_id (int): User ID.

        Returns:
            Performances: The best performances of the user.
        """
        performance_data = (await self.get_performances(user_id=user_id)).model_dump()

        for concept in performance_data.keys():
            for process in performance_data[concept].keys():
                performance_data[concept][process] = (
                    max(performance_data[concept][process])
                    if len(performance_data[concept][process]) > 0
                    else 0
                )

        performances = Performances.model_validate(performance_data)
        return performances

    async def get_average_performances(
        self,
        user_id: int,
    ) -> Performances:
        """Get the average performances of a user.

        Args:
            user_id (int): User ID.

        Returns:
            Performances: The average performances of the user.
        """
        performance_data = (await self.get_performances(user_id=user_id)).model_dump()

        for concept in performance_data.keys():
            for process in performance_data[concept].keys():
                performance_data[concept][process] = round(
                    sum(performance_data[concept][process])
                    / len(performance_data[concept][process])
                    if len(performance_data[concept][process]) > 0
                    else 0,
                    2,
                )

        performances = Performances.model_validate(performance_data)
        return performances

    async def get_recent_best_performances(
        self,
        user_id: int,
        timedelta: datetime.timedelta,
    ):
        """Get the recent best performances of a user.

        Args:
            user_id (int): User ID.
            timedelta (datetime.timedelta): Time delta to filter the performances.

        Returns:
            Performances: The recent best performances of the user.
        """
        performance_data = (
            await self.get_performances(user_id=user_id, timedelta=timedelta)
        ).model_dump()

        for concept in performance_data.keys():
            for process in performance_data[concept].keys():
                performance_data[concept][process] = (
                    max(performance_data[concept][process])
                    if len(performance_data[concept][process]) > 0
                    else 0
                )

        performances = Performances.model_validate(performance_data)
        return performances

    async def get_recent_average_performances(
        self,
        user_id: int,
        timedelta: datetime.timedelta,
    ) -> Performances:
        """Get the recent average performances of a user.

        Args:
            user_id (int): User ID.
            timedelta (datetime.timedelta): Time delta to filter the performances.

        Returns:
            Performances: The recent average performances of the user.
        """
        performance_data = (
            await self.get_performances(user_id=user_id, timedelta=timedelta)
        ).model_dump()

        for concept in performance_data.keys():
            for process in performance_data[concept].keys():
                performance_data[concept][process] = round(
                    sum(performance_data[concept][process])
                    / len(performance_data[concept][process])
                    if len(performance_data[concept][process]) > 0
                    else 0,
                    2,
                )

        performances = Performances.model_validate(performance_data)
        return performances

    async def get_performance_trends(
        self,
        user_id: int,
        timedelta: Optional[datetime.timedelta] = None,
    ) -> PerformanceTrends:
        """Get the performance trends of a user.

        Args:
            user_id (int): User ID.
            timedelta (datetime.timedelta, optional): Time delta to filter the performances. Defaults to None.

        Returns:
            PerformanceTrends: The performance trends of the user.
        """
        performances = (
            await self.get_performances(user_id=user_id, timedelta=timedelta)
        ).model_dump()

        result = {}

        for concept in performances.keys():
            result[concept] = {}
            for process in performances[concept].keys():
                if len(performances[concept][process]) < 2:
                    result[concept][process] = 0
                    continue
                x = np.arange(len(performances[concept][process]))
                y = np.array(performances[concept][process])

                if x.size <= 1:
                    result[concept][process] = Trend.STABLE
                    continue

                gradient = round(np.polyfit(x, y, 1)[0], 2)
                if 1 < gradient:
                    result[concept][process] = Trend.INCREASING_STRONG
                elif 0 < gradient <= 1:
                    result[concept][process] = Trend.INCREASING_SLIGHT
                elif -1 <= gradient < 0:
                    result[concept][process] = Trend.DECEASING_SLIGHT
                elif gradient < -1:
                    result[concept][process] = Trend.DECEASING_STRONG
                else:
                    result[concept][process] = Trend.STABLE

        performance_trends = PerformanceTrends.model_validate(result)
        return performance_trends

    async def get_performance_date_data(
        self,
        user_id: int,
        timedelta: Optional[datetime.timedelta] = None,
    ) -> PerformanceDateData:
        """Get the performance date data of a user.

        Args:
            user_id (int): User ID.
            timedelta (datetime.timedelta, optional): Time delta to filter the performances. Defaults to None.

        Returns:
            PerformanceDateData: The performance date data of the user.
        """

        def _get_average(sub_questions: List[CompletedSubQuestion]) -> float:
            return round(
                sum(sub_question.performance.value for sub_question in sub_questions)
                / len(sub_questions),
                2,
            )

        sub_questions = await self.user_manager.get_completed_sub_questions(
            user_id=user_id
        )
        sub_questions = [
            sub_question
            for sub_question in sub_questions
            if timedelta is None
            or sub_question.created_at.astimezone(datetime.timezone.utc)
            > datetime.datetime.now(datetime.timezone.utc) - timedelta
        ]

        dates = []
        for sub_question in sub_questions:
            date: datetime.datetime = sub_question.created_at.astimezone(
                pytz.timezone("Pacific/Auckland")
            )
            date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            if date not in dates:
                dates.append(date)
        dates.sort()

        performances = []
        for i in range(len(dates)):
            performances.append(
                _get_average(
                    [
                        sub_question
                        for sub_question in sub_questions
                        if sub_question.created_at.astimezone(
                            pytz.timezone("Pacific/Auckland")
                        ).replace(hour=0, minute=0, second=0, microsecond=0)
                        == dates[i]
                    ]
                )
            )

        performance_date_data = PerformanceDateData(
            performances=performances, dates=dates
        )
        return performance_date_data

    async def get_class_performances(
        self,
        class_id: int,
    ) -> Performances:
        """Get the performances of a class.

        Args:
            class_id (int): Class ID.

        Returns:
            Performances: The performances of the class.
        """
        class_ = await self.user_manager.get_class_by_id(class_id)

        if class_ is None:
            raise ClassIdInvalid(f"Class with id {class_id} not found!")

        performances = {
            "operations_on_numbers": {
                "formulate": 0,
                "apply": 0,
                "explain": 0,
            },
            "mathematical_relationships": {
                "formulate": 0,
                "apply": 0,
                "explain": 0,
            },
            "spatial_properties_and_representations": {
                "formulate": 0,
                "apply": 0,
                "explain": 0,
            },
            "location_and_navigation": {
                "formulate": 0,
                "apply": 0,
                "explain": 0,
            },
            "measurement": {
                "formulate": 0,
                "apply": 0,
                "explain": 0,
            },
            "statistics_and_data": {
                "formulate": 0,
                "apply": 0,
                "explain": 0,
            },
            "elements_of_chance": {
                "formulate": 0,
                "apply": 0,
                "explain": 0,
            },
        }
        for student in class_.students:
            student_performances = (
                await self.get_recent_average_performances(
                    user_id=student.id, timedelta=datetime.timedelta(days=30)
                )
            ).model_dump()
            for concept in ConceptType.__members__.keys():
                for process in ProcessType.__members__.keys():
                    concept = concept.lower()
                    process = process.lower()
                    performances[concept][process] += student_performances[concept][
                        process
                    ] / len(class_.students)

        for concept in ConceptType.__members__.keys():
            for process in ProcessType.__members__.keys():
                concept = concept.lower()
                process = process.lower()
                performances[concept][process] = round(
                    performances[concept][process], 2
                )

        performances = Performances.model_validate(performances)

        return performances

    async def get_performances(
        self,
        user_id: int,
        timedelta: Optional[datetime.timedelta] = None,
    ) -> PerformancesData:
        """Get the performances of a user.

        Args:
            user_id (int): User ID.
            timedelta (datetime.timedelta, optional): Time delta to filter the performances. Defaults to None.

        Returns:
            PerformancesData: The performances of the user.
        """
        sub_questions = await self.user_manager.get_completed_sub_questions(
            user_id=user_id
        )

        # remove duplicates, take the lastest ones
        unique_sub_questions: Dict[int, CompletedSubQuestion] = {}
        for sub_question in sub_questions:
            if (
                timedelta is not None
                and sub_question.created_at.astimezone(datetime.timezone.utc)
                < datetime.datetime.now(datetime.timezone.utc) - timedelta
            ):
                continue
            if sub_question.sub_question.id not in unique_sub_questions:
                unique_sub_questions[sub_question.sub_question.id] = sub_question
            else:
                if sub_question.created_at.astimezone(
                    datetime.timezone.utc
                ) > unique_sub_questions[
                    sub_question.sub_question.id
                ].created_at.astimezone(datetime.timezone.utc):
                    unique_sub_questions[sub_question.sub_question.id] = sub_question

        result = {
            "operations_on_numbers": {
                "formulate": [],
                "apply": [],
                "explain": [],
            },
            "mathematical_relationships": {
                "formulate": [],
                "apply": [],
                "explain": [],
            },
            "spatial_properties_and_representations": {
                "formulate": [],
                "apply": [],
                "explain": [],
            },
            "location_and_navigation": {
                "formulate": [],
                "apply": [],
                "explain": [],
            },
            "measurement": {
                "formulate": [],
                "apply": [],
                "explain": [],
            },
            "statistics_and_data": {
                "formulate": [],
                "apply": [],
                "explain": [],
            },
            "elements_of_chance": {
                "formulate": [],
                "apply": [],
                "explain": [],
            },
        }

        for sub_question in unique_sub_questions.values():
            concept = sub_question.sub_question.concept.name.lower()
            process = sub_question.sub_question.process.name.lower()
            performance = sub_question.performance.value

            result[concept][process].append(performance)

        performances = PerformancesData.model_validate(result)
        return performances
