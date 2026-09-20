"""Compose two different mocked study services on one event loop."""

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class StudyDashboard:
    course_title: str
    completed_lessons: int


async def load_course_title() -> str:
    await asyncio.sleep(0)
    return "Python core"


async def count_completed_lessons() -> int:
    await asyncio.sleep(0)
    return 4


async def build_study_dashboard() -> StudyDashboard:
    course_title, completed_lessons = await asyncio.gather(
        load_course_title(),
        count_completed_lessons(),
    )
    return StudyDashboard(
        course_title=course_title,
        completed_lessons=completed_lessons,
    )


def main() -> None:
    dashboard = asyncio.run(build_study_dashboard())
    print(f"{dashboard.course_title}: {dashboard.completed_lessons} lessons complete")


if __name__ == "__main__":
    main()
