"""
@author: Mohamed Hassan
The Functions that drive my app.
"""
import requests
import bs4
from colorama import Fore, Style


# Type Hint Aliases
Url = str
Video = bytes


def print_success(arg: str):
    print(f"{Fore.GREEN} {arg} {Style.RESET_ALL}")


def print_failure(arg: str):
    print(f"{Fore.RED} {arg} {Style.RESET_ALL}")


def log(msg: str):
    with open("./log.txt", "w+") as f:
        f.write(msg)
    print_failure(msg)


def filter_courses(tag: bs4.element.Tag) -> bool:
    if (
        tag.name != 'a' or
        tag.parent.name != 'li' or
        tag.parent.get('class') is None
    ):
        return False
    return 'book-cover' in tag.parent.get('class')


def get_courses_urls(GRADE_URL: Url, needed: list[str]) -> dict[str, Url]:
    response: requests.Response = requests.get(GRADE_URL)
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
    response: requests.Response = requests.get(course_url)
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


def get_links(url: Url, links: list[str]) -> dict[str, Url]:
    """Fetches The links of required_names from the link

    Args:
        link (str): The link of the lesson's page

    Returns:
        dict[str, str]: the title of the page and its link.
    """
    response: requests.Response = requests.get(url)
    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(response.text, "lxml")
    try:
        lesson_menu = soup.find(class_="components").findChild("ul")
    except AttributeError as err:
        with open("log.txt", "w") as f:
            f.write(str(err))
        print(f"LOG ERROR: {err}\n unordered list isn't \
              found in the components class in the soup")

    child: bs4.element.Tag
    result: dict[str, str] = {}
    for child in lesson_menu.children:
        if isinstance(child, bs4.NavigableString):
            continue

        result_link = child.findChild("a", recursive=True)
        # Checks the title of the current link
        # if the title matches one of tPhe needed ones
        # we mark it as needed and add its link and title to
        # the return value.
        for title in result_link:
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


def filter_subtitles(tag):
    return tag.name == "track" and tag["srclang"] in ["ar", "en"]


def download_video(link: Url) -> tuple[Video, dict[str, str]]:
    """Downloads the video from a link.
       the video source must be visible in the page"""

    response: requests.Response = requests.get(link)
    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(response.text, "lxml")
    video_player = soup.find(id="NagwaLitePlayer")
    # limits to two so it won't keep running after finding english and arabic.
    subtitles_bs4 = video_player.find_all(filter_subtitles, limit=2)
    subtitles: dict[str, str] = {}

    for subtitle in subtitles_bs4:
        subtitle_link = subtitle["src"]
        # ex: en->(the subtitle file after being downloaded)
        subtitles[subtitle["srclang"]] = requests.get(subtitle_link).text

    video_link = video_player.find("source")["src"]

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
    # how to do a V
    ...
