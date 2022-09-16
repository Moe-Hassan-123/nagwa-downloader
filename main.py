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
    PLAN: str = "Lesson Plan"
    VIDEO: str = "Lesson Video"
    PRESENTATION: str = "Lesson Presentation"
    PLAYLIST: str = "Lesson Playlist"
    EXPLAINER: str = "Lesson Explainer"


@dataclass
class Lesson:
    """Class that Saves the data of the current lesson"""

    title: str
    path: pathlib.Path
    main_link: str
    links: dict[Link, str]


def save_video(lesson: Lesson):
    video_path = lesson.path / "Lesson Video"
    video_path.mkdir(parents=True, exist_ok=True)

    # If video already exists, return.
    if (video_path / "Video.mp4").exists():
        Func.print_success("Video Already Exists")
        return

    try:
        video, subtitles = Func.download_video(lesson.links[Link.VIDEO])
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


def save_questions_playlist(lesson: Lesson):
    questions_path: pathlib.Path = lesson.path / "Questions Videos"
    questions_path.mkdir(parents=True, exist_ok=True)
    # videos: dict[str, str] = Func.get_playlist(lesson.links[Link.PLAYLIST])

    # os(lesson.links[Links.PLAYLIST])


def main():
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
                lesson.path = course_path / unit_title / lesson.title
                lesson.path.mkdir(parents=True, exist_ok=True)
                lesson.links = Func.get_links(lesson.main_link, Link.list())
                print(lesson.links)
                msg = f"Successfully got all links for the {lesson.title}"
                Func.print_success(msg)
                # Create the required paths.

                save_video(lesson)
                save_questions_playlist(lesson)


if __name__ == "__main__":
    main()
