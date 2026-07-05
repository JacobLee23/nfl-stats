"""
Interface for scraping NFL team pages
"""

import importlib.resources
import io
import json
import logging
import re
import typing

import bs4
import numpy as np
import pandas as pd
import requests

from ._http import HEADERS, TIMEOUT
from ._meta import MultitonMeta

LOGGER = logging.getLogger(__name__)

with (importlib.resources.files("nfl_stats") / "data" / "team-abbreviations.json").open() as file:
    TEAMS = json.load(file)

class _Ranking(typing.NamedTuple):
    """
    Models the intra-division ranking of a team

    .. py:attribute:: rank

        The intra-division rank of the team

    .. py:attribute:: conference

        The conference to which the team belongs (either `"AFC"` or `"NFC"`)

    .. py:attribute:: division

        The division to which the team belongs (one of `"East"`, `"North"`, `"South"`, or `"West"`)
    """
    rank: int
    conference: str
    division: str

class _Record(typing.NamedTuple):
    """
    Models a team record

    .. py:attribute:: win

        The number of games won by the team

    .. py:attribute:: loss

        The number of games lost by the team

    .. py:attribute:: tie

        The number of games tied by the team
    """
    win: int
    loss: int
    tie: int

    def __str__(self) -> str:
        return f"{self.win}-{self.loss}-{self.tie}"

class _Metadata(typing.NamedTuple):
    """
    A collection of team metadata

    .. py:attribute:: name

        The name of the team

    .. py:attribute:: ranking

        The intra-division ranking of the team

    .. py:attribute:: record

        The record of the team
    """
    name: str
    ranking: _Ranking
    record: _Record

class Team(metaclass=MultitonMeta):
    """
    Interface for scraping a team page
    """
    _instances: typing.Dict[str, "Team"] = {}

    _url = "https://nfl.com/teams/{team_id}"

    _name_class = "nfl-c-team-header__title"
    _ranking_class = "nfl-c-team-header__ranking"
    _record_class = "nfl-c-team-header__stats"
    _stats_class = "nfl-o-team-h2h-stats"

    _ranking_regex = re.compile(r"^([1-4])(st|nd|rd|th) (AFC|NFC) (East|North|South|West)$")
    _record_regex = re.compile(r"^(\d+) - (\d+) - (\d+)$")
    _fraction_regex = re.compile(r"^(\d+) / (\d+)$")

    _stats_dtypes = {
        # First Downs
        ("1D", "TOT"): "int64", ("1D", "RUSH"): "int64", ("1D", "PASS"): "int64",
        ("1D", "PEN"): "int64",

        # Third Downs
        ("3D%", "CMP"): "int64", ("3D%", "ATT"): "int64",

        # Fourth Downs
        ("4D%", "CMP"): "int64", ("4D%", "ATT"): "int64",

        # Total Offense
        ("OFF", "YD"): "int64", ("OFF", "ATT"): "int64", ("OFF", "AVG"): "float64",

        # Rushing Offense
        ("RUSH", "YD"): "int64", ("RUSH", "ATT"): "int64", ("RUSH", "AVG"): "float64",

        # Passing Offense
        ("PASS", "YD"): "int64", ("PASS", "CMP"): "int64", ("PASS", "ATT"): "int64",
        ("PASS", "INT"): "int64", ("PASS", "AVG"): "float64",

        # Total Defense
        ("SCK", "TOT"): "int64",

        # Field Goals
        ("FG%", "CMP"): "int64", ("FG%", "ATT"): "int64",

        # Touchdowns
        ("TD", "TOT"): "int64", ("TD", "RUSH"): "int64", ("TD", "PASS"): "int64",
        ("TD", "RET"): "int64", ("TD", "DEF"): "int64",

        # Turnovers
        ("TO", "RATIO"): "float64"
    }
    _stats_columns = (
        ("1D", "TOT"), ("1D", "RUSH"), ("1D", "PASS"), ("1D", "PEN"),
        ("3D", "CMP"), ("3D", "ATT"),
        ("4D", "CMP"), ("4D", "ATT"),
        ("OFF", "YD"), ("OFF", "ATT"), ("OFF", "AVG"),
        ("RUSH", "YD"), ("RUSH", "ATT"), ("RUSH", "AVG"),
        ("PASS", "YD"), ("PASS", "CMP"), ("PASS", "ATT"), ("PASS", "INT"), ("PASS", "AVG"),
        ("SCK", "TOT"),
        ("FG", "CMP"), ("FG", "ATT"),
        ("TD", "TOT"), ("TD", "RUSH"), ("TD", "PASS"), ("TD", "RET"), ("TD", "DEF"),
        ("TO", "RATIO")
    )

    _metadata: _Metadata | None
    _roster: pd.DataFrame | None
    _stats: pd.DataFrame | None

    def __init__(self, team_abbr: str):
        """
        :param team_abbr: The abbreviation code of the team whose page to scrape
        """
        self._team_abbr = team_abbr
        try:
            self._team_id = TEAMS[team_abbr]
        except KeyError as err:
            raise ValueError(f"Invalid team abbreviation: {team_abbr!r}") from err

        self._metadata = None
        self._roster = None
        self._stats = None

    def __repr__(self) -> str:
        attributes = ", ".join(f"{k}={getattr(self, k)!r}" for k in ("team_abbr", "team_id", "url"))
        return f"{self.__class__.__name__}({attributes})"

    @classmethod
    def __instance_key__(cls, team_id: str) -> str:
        return team_id

    def _scrape_metadata(self) -> _Metadata:
        """
        Scrapes the team metadata from the team page.

        :return: The scraped team metadata
        """
        with requests.get(self.url, headers=HEADERS, timeout=TIMEOUT) as response:
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.text, features="lxml")

        # Scrape team name
        name_elem = soup.select_one(f"div.{self._name_class}")
        if name_elem is None:
            raise ValueError
        name = name_elem.text

        # Scrape team intra-division ranking
        ranking_elem = soup.select_one(f"div.{self._ranking_class}")
        if ranking_elem is None:
            raise ValueError
        ranking_match = self._ranking_regex.search(ranking_elem.text)
        if ranking_match is None:
            raise ValueError
        ranking_groups = ranking_match.groups()
        ranking = _Ranking(int(ranking_groups[0]), ranking_groups[2], ranking_groups[3])

        # Scrape team record
        record_elem = soup.select_one(f"div.{self._record_class}")
        if record_elem is None:
            raise ValueError
        record_match = self._record_regex.search(record_elem.text)
        if record_match is None:
            raise ValueError
        record_groups = record_match.groups()
        record = _Record(int(record_groups[0]), int(record_groups[1]), int(record_groups[2]))

        return _Metadata(name, ranking, record)

    def _scrape_roster(self) -> pd.DataFrame:
        """
        Scrapes the team roster from the team page.

        :return: The scraped team roster
        """
        with requests.get(f"{self.url}/roster", headers=HEADERS, timeout=TIMEOUT) as response:
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.text, features="lxml")

        # Scrape roster table
        table_elem = soup.select_one("table[summary='Roster']")
        if table_elem is None:
            raise ValueError
        buffer = io.StringIO(str(table_elem))
        tables = pd.read_html(buffer)
        if len(tables) == 0:
            raise ValueError
        dataframe = tables[0]

        # Post-process table data
        dataframe["No"] = dataframe["No"].astype("Int64")
        dataframe["Experience"] = dataframe["Experience"].replace("R", 0).astype(np.int64)

        return dataframe

    def _scrape_stats(self) -> pd.DataFrame:
        """
        Scrapes the team stats from the team page.

        :return: The scraped team stats
        """
        dataframe = pd.DataFrame(
            index=[self._team_abbr, "OPP"], columns=pd.MultiIndex(levels=[[], []], codes=[[], []])
        )

        with requests.get(f"{self.url}/stats", headers=HEADERS, timeout=TIMEOUT) as response:
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.text, features="lxml")

        # Scrape stats table
        for list_item in soup.select(f"div.{self._stats_class} > ul > li"):
            label_container = list_item.select_one(f"div.{self._stats_class}__label")
            value_containers = list_item.select(f"div.{self._stats_class}__value")
            if label_container is None or len(value_containers) != 2:
                raise ValueError

            surlabel_elem = label_container.select_one("span:first-child")
            if surlabel_elem is None:
                raise ValueError

            sublabel_elems = label_container.select(
                f"span.{self._stats_class}__label--child"
                f":not(span.{self._stats_class}__label--short)"
            )
            if sublabel_elems:
                for idx, value_container in zip(dataframe.index, value_containers):
                    value_elems = value_container.select("span")
                    if len(value_elems) != len(sublabel_elems):
                        raise ValueError
                    for sublabel_elem, value_elem in zip(sublabel_elems, value_elems):
                        dataframe.loc[
                            idx, (surlabel_elem.text, sublabel_elem.text)
                        ] = value_elem.text
            else:
                for idx, value_container in zip(dataframe.index, value_containers):
                    fraction_match = self._fraction_regex.search(value_container.text)
                    if fraction_match is None:
                        dataframe.loc[idx, (surlabel_elem.text, "")] = value_container.text
                    else:
                        dataframe.loc[
                            idx, (surlabel_elem.text, "CMP")
                        ] = int(fraction_match.group(1))
                        dataframe.loc[
                            idx, (surlabel_elem.text, "ATT")
                        ] = int(fraction_match.group(2))

        # Post-process table data
        dataframe.columns = pd.MultiIndex.from_tuples(self._stats_dtypes)
        dataframe.replace("", np.nan, inplace=True)
        dataframe = dataframe.astype(self._stats_dtypes)
        dataframe.loc["OPP", ("TO", "RATIO")] = 1 / float(
            typing.cast(float, dataframe.loc[self._team_abbr, ("TO", "RATIO")])
        )

        return dataframe

    @property
    def team_abbr(self) -> str:
        """
        The abbreviation code of the team
        """
        return self._team_abbr

    @property
    def team_id(self) -> str:
        """
        The NFL ID of the team
        """
        return self._team_id

    @property
    def url(self) -> str:
        """
        The URL of the team page
        """
        return self._url.format(team_id=self._team_id)

    @property
    def metadata(self) -> _Metadata:
        """
        The scraped team metadata
        """
        if self._metadata is None:
            self._metadata = self._scrape_metadata()
        return self._metadata

    @property
    def roster(self) -> pd.DataFrame:
        """
        The scraped team roster
        """
        if self._roster is None:
            self._roster = self._scrape_roster()
        return self._roster.copy()

    @property
    def stats(self) -> pd.DataFrame:
        """
        The scraped team stats
        """
        if self._stats is None:
            self._stats = self._scrape_stats()
        return self._stats.copy()
