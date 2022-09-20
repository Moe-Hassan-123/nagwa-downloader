import logging
import pathlib
import helpers.functions as Func
from helpers.data import Link, Lesson, Url


def save_video(lesson: type[Lesson]) -> None:
    if lesson.links[Link.VIDEO] is None:
        return

    video_path = lesson.path / "Lesson Video"
    video_path.mkdir(parents=True, exist_ok=True)

    # If video already exists, return.
    if (video_path / "Video.mp4").exists():
        logging.info("Video Already Exists")
        return

    try:
        video, subtitles = Func.download_video(lesson.links[Link.VIDEO])
    except KeyError:
        logging.error(f"LESSON'S VIDEO NOT FOUND IN {lesson.title}")
        return

    logging.info("Successfully downloaded the video and subtitles")

    for lang, subtitle in subtitles.items():
        path_subs: pathlib.Path = video_path / f"subtitle_{lang}.vtt"
        with path_subs.open("w") as f:
            f.write(subtitle)
    vid_path: pathlib.Path = video_path / "Video.mp4"
    vid_path.write_bytes(video)
    logging.info("Successfuly Wrote the video and subtitles to disk.")


def save_questions_playlist(lesson: type[Lesson]) -> None:
    if lesson.links[Link.PLAYLIST] is None:
        return

    questions_path: pathlib.Path = lesson.path / "Questions Videos"
    questions_path.mkdir(parents=True, exist_ok=True)
    if any(questions_path.iterdir()):
        logging.info("Question Videos Already Exist")
        return
    try:
        Videos = Func.get_playlist(lesson.links[Link.PLAYLIST])
    except ValueError as e:
        logging.error(f"{lesson.title}'s Playlist Page can't be accessed.\n{e}")
        return
    for title, video in Videos.items():
        title = Func.clean(title)
        video_path = questions_path / f"{title}.mp4"
        video_path.write_bytes(video)


def save_presentation(lesson: type[Lesson]) -> None:

    path: pathlib.Path = lesson.path / "Presentation"
    if lesson.links is None:
        return

    if lesson.links[Link.PRESENTATION] is None:
        return

    if path.exists():
        logging.info(f"Presentation for {lesson.title} already exists")
        return

    images: list[Func.Image.Image] = Func.get_presentation(
        lesson.links[Link.PRESENTATION]
    )
    logging.info("Saving The Presentation...")
    images[0].save(
        path, "PDF", resolution=100.0, save_all=True, append_images=images[1:]
    )
    logging.info("Succcessfully Downloaded Presentation")


def get_courses_urls(GRADE_URL: Url, needed: list[str]) -> dict[str, Url]:
    return Func.get_courses_urls(GRADE_URL, needed)


def get_links(url: Url, links: list[str]) -> dict[str, Url]:
    return Func.get_links(url, links)
