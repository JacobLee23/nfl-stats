"""
Regression tests for :py:mod:`nfl_stats._team`
"""

import pandas as pd
import pytest

from nfl_stats import Team
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

@pytest.mark.parametrize("team", TEAMS.keys(), indirect=True)
class TestTeam:
    """
    Regression tests for :py:mod:`nfl_stats._team.Team`
    """
    def test_metadata(self, team: Team):
        """
        Black-box regression test for :py:attr:`Team.metadata`

        :param team: A scraper for a team page
        """
        # Property should be read-only
        with pytest.raises(AttributeError):
            team.metadata = None

        # Sanity check
        assert team.metadata is not None

        # Validate contents of returned object
        assert team.metadata.name != ""
        assert team.metadata.ranking is not None
        assert team.metadata.ranking.rank in (1, 2, 3, 4)
        assert team.metadata.ranking.conference in ("AFC", "NFC")
        assert team.metadata.ranking.division in ("East", "North", "South", "West")
        assert team.metadata.record is not None
        assert all(isinstance(x, int) for x in team.metadata.record)

    def test_roster(self, team: Team):
        """
        Black-box regression test for :py:attr:`Team.roster`

        :param team: A scraper for a team page
        """
        # Property should be read-only
        with pytest.raises(AttributeError):
            team.roster = None

        # Sanity check
        assert team.roster is not None

        # Returned objects should be a copies of the internally stored object
        assert id(team.roster) != id(team.roster), (
            "Returned objects should be copies of the internally stored object"
        )

        # Validate contents of returned object
        columns = pd.Index(
            ["Player", "No", "Pos", "Status", "Height", "Weight", "Experience", "College"]
        )
        dtypes = pd.Series(
            ["str", "Int64", "str", "str", "int64", "int64", "int64", "str"],
            index=columns, dtype=object
        )
        assert team.roster.columns.equals(columns)
        assert team.roster.dtypes.equals(dtypes)
        assert not team.roster.empty

    def test_stats(self, team: Team):
        """
        Black-box regression test for :py:attr:`Team.stats`

        :param team: A scraper for a team page
        """
        # Property should be read-only
        with pytest.raises(AttributeError):
            team.stats = None

        # Sanity check
        assert team.stats is not None

        # Returned objects should be a copies of the internally stored object
        assert id(team.stats) != id(team.stats), (
            "Returned objects should be copies of the internally stored object"
        )

        # Validate contents of return object
        index = pd.Index([team.team_abbr, "OPP"])
        columns = pd.MultiIndex.from_tuples(Team._stats_dtypes.keys())
        assert team.stats.index.equals(index)
        assert team.stats.columns.equals(columns)
        assert not team.stats.empty
