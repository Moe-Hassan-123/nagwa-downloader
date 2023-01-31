"""
@author: Mohamed Hassan

Main Functionality of the app.
"""
import asyncio
import logging
from io import BytesIO
from time import sleep
from types import NoneType

import aiohttp
import bs4
import cairosvg
import requests
from PIL import Image

from helpers.data import Url, Video


def get_response(url: Url) -> None | requests.Response:
    """Helper Function used in getting a response from server
    if the response code wasn't OK it keeps requesting
    with 3 second delay between requests.
    """
    response: requests.Response = requests.get(url)
    count = 1
    while response.status_code != 200:
        if count == 50:
            return None
        sleep(3)
        response = requests.get(url)
        count += 1
    return response


def filter_courses(tag: bs4.element.Tag) -> bool:
    if tag.name != "a" or tag.parent.name != "li" or tag.parent.get("class") is None:
        return False
    return "book-cover" in tag.parent.get("class")


def get_courses_urls(GRADE_URL: Url, needed: list[str]) -> dict[str, Url]:

    response = get_response(GRADE_URL)
    if response is None:
        logging.error(f"{GRADE_URL} Can't be reached after 50 tries.")
        return {}

    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(response.text, "lxml")
    links: bs4.element.ResultSet = soup.find_all(filter_courses)
    result = {}
    for link in links:
        name = link.find("h4").text
        if name in needed:
            result[name] = link["href"]
    return result


def get_lessons_urls(course_url: Url) -> dict[str, dict[str, Url]]:
    """Grabs the Urls of the lessons of a given course.

    Args:
        course_url (str): the url of the page containing the lessons.

    Returns:
        dict[str, dict[str, str]]: a dictionary that has unit titles as keys
        andthe values as another dict of the lesson title
        as key and lesson link as values.
    """
    response = get_response(course_url)
    if response is None:
        logging.error(f"{course_url} Can't be reached after 50 tries.")
        return {}

    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(response.text, "lxml")
    # list-nested is the class where the curriculum lies.
    all = soup.find(class_="list-nested")
    units = all.children
    result = {}
    for unit in units:
        if unit == "\n":
            continue
        # unit is an element with 2 parts
        # navigableString as first and the second part is unorderedlist
        # I traverse through it as an iterable to assign -
        # the nav_string to title
        # and the unordered_list to the lessons.
        # I haven't found another way to traverse such element.
        it = iter(unit)
        title: str = next(it)
        title = title.strip()

        # Unordered list of the required elements.
        lessons_bs4: bs4.element.Tag = next(it)
        lessons = {}
        for lesson in lessons_bs4.children:
            # handle lesson being an empty string or a newline
            if isinstance(lesson, bs4.element.NavigableString):
                continue
            l: bs4.element.Tag = lesson.a
            link: str = l["href"]
            lesson_title: str = l.text.lstrip("Lesson: ")
            # Store each lesson as a key and its value is the link
            lessons[lesson_title] = link
        # Store the result for each unit and
        # make the value a list of the lessons.
        result[title] = lessons
    return result


def get_presentation(url: Url) -> list[Image.Image]:
    async def get_all(urls) -> list:
        async with aiohttp.ClientSession() as session:

            async def fetch(url):
                async with session.get(url) as response:
                    return await response.read()

            return await asyncio.gather(*[fetch(url) for url in urls])

    logging.info("Downloading the presentation...")

    response = get_response(url)
    if response is None:
        logging.error(f"{url} Can't be reached after 50 tries.")
        return []

    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(response.text, "lxml")
    slides_bs4: bs4.element.Tag = soup.find_all(alt="Slide")
    slides_links = [slide["src"] for slide in slides_bs4]
    images = []

    slides = asyncio.run(get_all(slides_links))
    logging.info("Processing the presentation...")
    for slide in slides:
        res = cairosvg.svg2png(bytestring=slide, scale=4, dpi=3000)
        # I had to convert to bytes as that's the form PIL library understands.
        res_bytes = BytesIO(res)
        rgba = Image.open(res_bytes)
        rgb = Image.new("RGB", rgba.size, (255, 255, 255))  # white background
        # Paste using alpha channel as mask
        rgb.paste(rgba, mask=rgba.split()[3])
        images.append(rgb)
    return images


def get_links(url: Url, links: list[str]) -> dict[str, Url]:
    """Fetches The links of required_names from the link

    Args:
        url (str): The link of the lesson's page
        links (list[str]): The title of the required links

    Returns:
        dict[str, str]: the title of the page and its link.
    """
    response = get_response(url)
    if response is None:
        logging.error(f"{url} Can't be reached after 50 tries.")
        return {}

    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(response.text, "lxml")
    if response.status_code != 200:
        logging.warning(f"response for {url} isn't OK it is: {response.status_code}")

    try:
        lesson_menu = soup.find(class_="components").findChild("ul")
    except AttributeError as err:
        logging.error(err)
        return {}

    result: dict[str, str] = {}
    child: bs4.element.Tag
    for child in lesson_menu.children:
        if isinstance(child, bs4.NavigableString):
            continue

        result_link = child.findChild("a", recursive=True)

        for title in result_link:
            # we need to only match a string.
            if not isinstance(title, bs4.NavigableString):
                continue
            title = title.strip()
            if title in links:
                break
        # title not found
        else:
            continue

        result[title] = result_link["href"]

    return result


def filter_subtitles(tag: bs4.element.Tag):
    return tag.name == "track" and tag["srclang"] in ["ar", "en"]


def download_video(link: Url) -> tuple[Video, dict[str, str]]:
    """Downloads the video from a link.
    the video source must be visible in the page
    """

    response = get_response(link)
    if response is None:
        logging.error(f"{link} Can't be reached after 50 tries.")
        return (b"", {})
    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(response.text, "lxml")
    video_player = soup.find(id="NagwaLitePlayer")
    # limits to two so it won't keep running after finding english and arabic.
    if isinstance(video_player, NoneType):
        return b"", {}
    subtitles_bs4 = video_player.find_all(filter_subtitles, limit=2)
    subtitles: dict[str, str] = {}

    for subtitle in subtitles_bs4:
        subtitle_link = subtitle["src"]
        # ex: en->(the subtitle file after being downloaded)
        subtitles[subtitle["srclang"]] = requests.get(subtitle_link, verify=False).text

    video_link = video_player.find("source")["src"]

    # If we have a list of videos, then we only need one video.
    # Generally, this happens when there is more than one resolution.
    if isinstance(video_link, list):
        video_link = video_link[0]

    video: Video = requests.get(video_link).content
    return video, subtitles


def get_playlist(link: Url) -> dict[str, Video]:
    """Downloads a playlist from nagwa.

    Args:
        link (str): the link where the playlist lies.

    Returns:
        dict[str, str]: a dictionary of the video name as keys and -
        the video itself as a value.
    """

    response = get_response(link)
    if response is None:
        logging.error(f"{link} Can't be reached after 50 tries.")
        return {}

    # FIXME potentially not needed
    # some times we don't get a right response from the server
    # idk if this is the case or not...
    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(response.text, "lxml")
    videos: bs4.element.Tag = soup.find(class_="videos-list")
    result: dict[str, Video] = {}
    video: bs4.element.Tag
    repeated = 0
    for video in videos.find_all("li"):
        if isinstance(video, bs4.NavigableString):
            continue
        info_parent: bs4.element.Tag = video.find("h4")
        info: bs4.element.Tag = info_parent.find("a")
        video = download_video(info["href"])[0]
        if video == b"":
            continue
        title = clean((info.string).strip())
        if result.get(title) is not None:
            title += f" ({repeated})"
            repeated += 1
        result[title] = video
        logging.info(f"{title} is Downloaded Successfuly")
    return result


def clean(string: str) -> str:
    """Removes any non-ascii characters

    Args:
        string (str): string to be cleaned

    Returns:
        str: the same string with non-ascii characters replaced
    """
    return "".join([c for c in string if ord(c) < 128 and c not in ["\\", "/"]])
