"""A Script that downloads videos from nagwa website
"""

from dataclasses import dataclass
from enum import Enum
import pathlib

import functions as Func

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


class ExtendedEnum(Enum):

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class Link (ExtendedEnum):
    PLAN: Func.Url = "Lesson Plan"
    VIDEO: Func.Url = "Lesson Video"
    PRESENTATION: Func.Url = "Lesson Presentation"
    PLAYLIST: Func.Url = "Lesson Playlist"
    EXPLAINER: Func.Url = "Lesson Explainer"


@dataclass
class Lesson:
    """Class that Saves the data of the current lesson"""

    title: str
    path: pathlib.Path
    main_link: Func.Url
    links: dict[Func.Url, str]


def save_video(lesson: Lesson) -> None:
    video_path = lesson.path / "Lesson Video"
    video_path.mkdir(parents=True, exist_ok=True)

    # If video already exists, return.
    if (video_path / "Video.mp4").exists():
        Func.print_success("Video Already Exists")
        return

    try:
        video, subtitles = Func.download_video(lesson.links[Link.VIDEO.value])
    except KeyError:
        Func.log(f"LESSON'S VIDEO NOT FOUND IN {lesson.title}")
        return

    Func.print_success("Successfully downloaded the video and subtitles")

    for lang, subtitle in subtitles.items():
        path_subs: pathlib.Path = video_path / f"subtitle_{lang}.vtt"
        with path_subs.open("w") as f:
            f.write(subtitle)
    vid_path: pathlib.Path = video_path / "Video.mp4"
    with vid_path.open("wb") as f:
        f.write(video)
    Func.print_success("Successfuly Wrote the video and subtitles to disk.")


def save_questions_playlist(lesson: Lesson) -> None:
    questions_path: pathlib.Path = lesson.path / "Questions Videos"
    questions_path.mkdir(parents=True, exist_ok=True)
    if any(questions_path.iterdir()):
        Func.print_success("Question Videos Already Exist")
        return
    Videos = Func.get_playlist(lesson.links[Link.PLAYLIST.value])
    for title, video in Videos.items():
        video_path = questions_path / f"{title.strip()}.mp4"
        with video_path.open("wb") as f:
            f.write(video)


def main() -> None:
    if not (courses := Func.get_courses_urls(GRADE_URL, needed_courses)):
        Func.print_failure("Get Courses Urls returned Nothing.")
        return

    Func.print_success("Succesfuly Downloaded Courses links.")
    for course_title, course_link in courses.items():
        print(f"\nCURRENT Subject is {course_title} \n")
        # Create a directory for the co urse.
        course_path: pathlib.Path = pathlib.Path(f"./result/{course_title}")
        course_path.mkdir(parents=True, exist_ok=True)
        # Calls a function that graps the names and links of the lessons.
        curriculum: dict = Func.get_lessons_urls(course_link)
        print("Successfully Downloaded lessons links")

        for unit_title, unit in curriculum.items():
            print(f"\nCURRENT UNIT is  {unit_title} \n")
            lesson = Lesson

            for lesson.title, lesson.main_link in unit.items():
                lesson.links = Func.get_links(lesson.main_link, Link.list())

                lesson.path = course_path / unit_title / lesson.title
                lesson.path.mkdir(parents=True, exist_ok=True)
                msg = f"Successfully got all links for the {lesson.title}"
                Func.print_success(msg)

                save_video(lesson)
                save_questions_playlist(lesson)


if __name__ == "__main__":
    main()
