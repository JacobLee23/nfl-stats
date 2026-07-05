"""
Unit tests for :py:mod:`nfl_stats.team`
"""

import io
import typing

import bs4
import pandas as pd
import pytest
import requests

from nfl_stats import Team
from nfl_stats._http import HEADERS, TIMEOUT
from nfl_stats._team import TEAMS

@pytest.fixture(scope="module")
def team(request: pytest.FixtureRequest) -> Team:
    """
    Constructs a scraper for a team page.

    :param request: A fixture request containing the team abbreviation code
    :return: A scraper for the specified team page
    """
    team_abbr = request.param
    return Team(team_abbr)

@pytest.fixture(scope="module")
def response(
    request: pytest.FixtureRequest, team: Team
) -> typing.Generator[requests.Response, None, None]:
    """
    Sends an HTTP request for a subpage of the team page

    :param request: A fixture request containing the subpage of the team page to request
    :param team: A scraper for the specified team page
    :return: The HTTP response
    """
    subpage = request.param
    with requests.get(f"{team.url}{subpage}", headers=HEADERS, timeout=TIMEOUT) as response:
        yield response

@pytest.fixture(scope="module")
def soup(response: requests.Response) -> bs4.BeautifulSoup:
    """
    Parses the HTML document contained in the body of an HTTP response

    :param response: An HTTP response to parse
    :return: The parsed HTML document contained in the body of the HTTP response
    """
    return bs4.BeautifulSoup(response.text, features="lxml")

class TestTeam:
    """
    Unit tests for :py:class:`nfl_stats.team.Team`.
    """
    @pytest.mark.parametrize("response", ["/", "/roster", "/stats"], indirect=True)
    @pytest.mark.parametrize("team", TEAMS.keys(), indirect=True)
    def test_url(self, response: requests.Response):
        """
        Tests the HTTP response received from sending an HTTP request to one of the
        subpages of a team page.

        :param response: An HTTP response
        """
        assert response.status_code == requests.codes.ok
        assert response.headers["content-type"] == "text/html"

    @pytest.mark.parametrize("response", ["/"], indirect=True)
    @pytest.mark.parametrize("team", TEAMS.keys(), indirect=True)
    def test_metadata(self, soup: bs4.BeautifulSoup):
        """
        White-box unit test for :py:attr:`Team.metadata`

        :param soup: The parsed HTML document of the team _/_ subpage
        """
        name_elem = soup.select_one(f"div.{Team._name_class}")
        assert name_elem is not None
        assert name_elem.text

        ranking_elem = soup.select_one(f"div.{Team._ranking_class}")
        assert ranking_elem is not None
        assert ranking_elem.text
        assert Team._ranking_regex.search(ranking_elem.text) is not None

        record_elem = soup.select_one(f"div.{Team._record_class}")
        assert record_elem is not None
        assert record_elem.text
        assert Team._record_regex.search(record_elem.text) is not None

    @pytest.mark.parametrize("response", ["/roster"], indirect=True)
    @pytest.mark.parametrize("team", TEAMS.keys(), indirect=True)
    def test_roster(self, soup: bs4.BeautifulSoup):
        """
        White-box unit test for :py:attr:`Team.roster`

        :param soup: The parsed HTML document of the team _/roster_ subpage
        """
        table_elem = soup.select_one("table[summary='Roster']")
        assert table_elem is not None
        buffer = io.StringIO(str(table_elem))
        tables = pd.read_html(buffer)
        assert len(tables) == 1

    @pytest.mark.parametrize("response", ["/stats"], indirect=True)
    @pytest.mark.parametrize("team", TEAMS.keys(), indirect=True)
    def test_stats(self, soup: bs4.BeautifulSoup):
        """
        White-box unit test for :py:attr:`Team.stats`

        :param soup: The parsed HTML document of the team _/stats_ subpage
        """
        list_items = soup.select(f"div.{Team._stats_class} > ul > li")
        assert list_items

        for list_item in list_items:
            label_container = list_item.select_one(f"div.{Team._stats_class}__label")
            assert label_container is not None
            assert label_container.text

            value_containers = list_item.select(f"div.{Team._stats_class}__value")
            assert value_containers
            assert len(value_containers) == 2

            surlabel_elem = label_container.select_one("span:first-child")
            assert surlabel_elem is not None
            assert surlabel_elem.text

            sublabel_elems = label_container.select(
                f"span.{Team._stats_class}__label--child"
                f":not(span.{Team._stats_class}__label--short)"
            )
            if sublabel_elems:
                assert all(e.text for e in sublabel_elems)
                for value_container in value_containers:
                    value_elems = value_container.select("span")
                    assert len(value_elems) == len(sublabel_elems)
                    assert all(e.text for e in value_elems)
            else:
                for value_container in value_containers:
                    value = value_container.text
                    if "/" in value:
                        assert Team._fraction_regex.search(value) is not None
