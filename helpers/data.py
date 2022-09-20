"""
@author: Mohamed Hassan

A Module for Data-orinted classes and variables.
used in facilitation of dealing with data in my app.
"""
from enum import Enum
from dataclasses import dataclass
import pathlib

Url = str
Video = bytes


class ExtendedEnum(str, Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


# inherits from str to allow it to be used as an entry to a
# dictionary which is its main usage.
class Link(ExtendedEnum):
    PLAN: Url = "Lesson Plan"
    VIDEO: Url = "Lesson Video"
    PRESENTATION: Url = "Lesson Presentation"
    PLAYLIST: Url = "Lesson Playlist"
    EXPLAINER: Url = "Lesson Explainer"


@dataclass
class Lesson:
    """Class that Saves the data of the current lesson"""

    title: str
    links: dict[str, Url]
    main_link: Url
    path: pathlib.Path
