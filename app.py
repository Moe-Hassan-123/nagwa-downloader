"""A Script that downloads videos from nagwa website
"""
import logging
import pathlib
from multiprocessing import Pool

# Suppress Warnings for insecure https requests.
import urllib3

import helpers.module as module

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GRADE = 11
GRADE_URL = f"https://www.nagwa.com/en/eg/grades/{GRADE}/"

needed_courses = [
    "Pure Mathematics",
    "Mathematics Applications",
    "Physics",
    "Chemistry",
    "Biology",
    "English",
    "Information and Communication Technology",
]


def download_lesson(course_path, unit_title, lesson: type[module.Lesson]) -> None:

    lesson.path = course_path / unit_title / lesson.title
    lesson.links = module.get_links(lesson.main_link, module.Link.list())
    if lesson.links == {}:
        return
    logging.info(f"Successfully got all links for the {lesson.title}")

    module.save_presentation(lesson)
    module.save_video(lesson)
    module.save_questions_playlist(lesson)


def download_unit(course_path, unit_title: str, lessons: dict) -> None:

    logging.info(f"Download Unit: {unit_title}")

    lesson = module.Lesson
    for lesson.title, lesson.main_link in lessons.items():
        download_lesson(course_path, unit_title, lesson)


def download_course(course_title, course_link) -> None:

    logging.info(f"Downloading Course: {course_title}")
    curriculum: dict = module.Func.get_lessons_urls(course_link)

    course_path: pathlib.Path = pathlib.Path(f"/media/mohamed/Storage1/result/{course_title}")
    for title, links in curriculum.items():
        download_unit(course_path, title, links)


def main() -> None:

    if not (courses := module.Func.get_courses_urls(GRADE_URL, needed_courses)):
        logging.error("Get Courses Urls returned Nothing.")
        return

    logging.info("Starting to Download Courses...")
    with Pool() as pool:
        pool.starmap(download_course, courses.items())


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%I:%M:%S %p",
        level=logging.INFO,
        handlers=[logging.FileHandler("nagwa.log", mode="w"), logging.StreamHandler()],
    )
    main()
