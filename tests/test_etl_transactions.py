import pandas as pd

from etl.load_historical import clean_value, insert_stat_group, load_season_file


class FakeCursor:
    def __init__(self, fail_table=None):
        self.fail_table = fail_table
        self.calls = []
        self.savepoints = set()

    def execute(self, sql, params=None):
        self.calls.append(sql)
        if sql.startswith("SAVEPOINT "):
            self.savepoints.add(sql.split()[1])
        elif sql.startswith("RELEASE SAVEPOINT "):
            self.savepoints.discard(sql.split()[2])
        elif sql.startswith("ROLLBACK TO SAVEPOINT "):
            assert sql.split()[3] in self.savepoints
        elif "INSERT INTO player_season_stats" in sql:
            self.result = (123,)
        elif "SELECT" in sql:
            self.result = None
        elif self.fail_table and f"INSERT INTO {self.fail_table}" in sql:
            raise RuntimeError("simulated stat-group failure")

    def fetchone(self):
        value = getattr(self, "result", None)
        self.result = None
        return value


def test_clean_value_converts_nan_to_none():
    assert clean_value(float("nan")) is None
    assert clean_value(12) == 12


def test_bad_row_rolls_back_to_row_savepoint(monkeypatch, tmp_path):
    path = tmp_path / "cleaned_2023-24.csv"
    data = {
        "player": ["Good", "Bad"],
        "nation": ["IE", "IE"],
        "pos": ["MF", "MF"],
        "squad": ["Team", "Team"],
        "comp": ["League", "League"],
        "age": [20, 21],
        "born": [2004, 2003],
        "Matches Played": [1, 1],
        "Avg Mins per Match": [90, 90],
        "Goals": [1, 1],
        "Assists": [0, 0],
        "Goals & Assists": [1, 1],
        "Non Penalty Goals": [1, 1],
        "Penalty Kicks Made": [0, 0],
        "Expected Goals": [0.5, 0.5],
        "Exp NPG": [0.5, 0.5],
    }
    pd.DataFrame(data).to_csv(path, index=False)
    # The transaction mechanics are exercised through a real failing stat-group.
    monkeypatch.setattr(
        "etl.load_historical.STAT_GROUP_TABLES",
        {"player_season_attacking": ["goals"]},
    )
    cursor = FakeCursor(fail_table="player_season_attacking")

    # Provide deterministic dimension IDs without a database.
    ids = iter([1, 2, 3, 4])
    def fake_get_or_create(*args, **kwargs):
        return next(ids)
    monkeypatch.setattr("etl.load_historical.get_or_create_id", fake_get_or_create)

    inserted, skipped = load_season_file(
        cursor, str(path),
        {"seasons": {}, "leagues": {}, "teams": {}, "players": {}},
    )
    assert inserted == 0
    assert skipped == 2
    assert any("ROLLBACK TO SAVEPOINT" in call for call in cursor.calls)
