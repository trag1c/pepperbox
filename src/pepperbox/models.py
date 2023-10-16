from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from functools import cached_property
from typing import Dict, TypeVar

import httpx

from .exceptions import PepperboxConnectionError

KT = TypeVar("KT")
VT = TypeVar("VT")

API_URL = "https://peps.python.org/api/peps.json"
BASE_CONTENT_URL = "https://raw.githubusercontent.com/python/peps/main/peps/pep-{:04}.{}"


class DottedDict(Dict[KT, VT]):
    __getattr__ = dict.__getitem__


class PEPData(DottedDict[str, "str | None"]):
    number: int
    title: str
    authors: str
    discussions_to: str | None
    status: str
    type: str
    topic: str
    created: str
    python_version: str | None
    post_history: str | None
    resolution: str | None
    requires: str | None
    replaces: str | None
    superseded_by: str | None
    url: str


_db = {int(k): PEPData(v) for k, v in httpx.get(API_URL).json().items()}


class PEPStatus(Enum):
    ACCEPTED = "Accepted"
    ACTIVE = "Active"
    DEFERRED = "Deferred"
    DRAFT = "Draft"
    FINAL = "Final"
    PROVISIONAL = "Provisional"
    REJECTED = "Rejected"
    REPLACED = "Replaced"
    SUPERSEDED = "Superseded"
    WITHDRAWN = "Withdrawn"


class PEPTopic(Enum):
    GOVERNANCE = "governance"
    PACKAGING = "packaging"
    RELEASE = "release"
    TYPING = "typing"


class PEPType(Enum):
    INFORMATIONAL = "Informational"
    PROCESS = "Process"
    STANDARD_TRACK = "Standards Track"


class PEP:
    def __init__(self, number: int, /) -> None:
        self._number = number
        data = _db[number]
        self._title = data.title
        self._authors = frozenset(data.authors.split(", "))
        self._discussions_to = data.discussions_to
        self._status = PEPStatus(data.status)
        self._type = PEPType(data.type)
        self._topics = list(map(PEPTopic, data.topic.split(", ") or []))
        self._created = (
            datetime
            .strptime(data.created, "%d-%b-%Y")
            .astimezone(timezone.utc)
            .date()
        )
        self._python_version = data.python_version
        self._post_history = data.post_history
        self._resolution = data.resolution
        self._requires = data.requires
        self._replaces = data.replaces
        self._superseded_by = data.superseded_by
        self._url = data.url
        self._source = ""
        self._source_url = ""

    def _fetch_source(self) -> None:
        for ext in ("rst", "txt"):
            url = BASE_CONTENT_URL.format(int(self), ext)
            resp = httpx.get(url)
            if resp.status_code == 200:
                self._source_url = url
                self._source = resp.content.decode()
                return
        raise PepperboxConnectionError("PEP content not found")

    @cached_property
    def source(self) -> str:
        if not self._source:
            self._fetch_source()
        return self._source

    @cached_property
    def source_url(self) -> str:
        if not self._source_url:
            self._fetch_source()
        return self._source_url

    @property
    def title(self) -> str:
        return self._title

    @property
    def authors(self) -> frozenset[str]:
        return self._authors

    @property
    def discussions_to(self) -> str | None:
        return self._discussions_to

    @property
    def status(self) -> PEPStatus:
        return self._status

    @property
    def type(self) -> PEPType:
        return self._type

    @property
    def topics(self) -> list[PEPTopic]:
        return self._topics

    @property
    def created(self) -> date:
        return self._created

    @property
    def python_version(self) -> str | None:
        return self._python_version

    @property
    def post_history(self) -> str | None:
        return self._post_history

    @property
    def resolution(self) -> str | None:
        return self._resolution

    @property
    def requires(self) -> str | None:
        return self._requires

    @property
    def replaces(self) -> str | None:
        return self._replaces

    @property
    def superseded_by(self) -> str | None:
        return self._superseded_by

    @property
    def url(self) -> str:
        return self._url

    def __int__(self) -> int:
        return self._number

    def __repr__(self) -> str:
        return f"PEP({int(self)})"
