import pandas as pd
import pytest

from etl.load_historical import load_and_clean_csv, season_label_from_filename


def test_season_label_from_filename():
    assert season_label_from_filename("cleaned_2017-18.csv") == "2017-2018"
    assert season_label_from_filename("cleaned_2023-24.csv") == "2023-2024"


def test_load_and_clean_csv_uses_utf8_and_normalises_columns(tmp_path):
    path = tmp_path / "cleaned_2023-24.csv"
    pd.DataFrame([{
        "rk": 1, "player": "Loïs Openda", "nation": "be BEL", "pos": "FW",
        "squad": "RB Leipzig", "comp": "Bundesliga", "age": 24, "born": 2000,
        "Matches Played": 1, "Avg Mins per Match": 90, "Goals": 1,
        "Goals Scored": 1, "Progressive Carries": 2, "carries_prgc": 2,
    }]).to_csv(path, index=False, encoding="utf-8")
    df = load_and_clean_csv(str(path))
    assert df.loc[0, "player_name"] == "Loïs Openda"
    assert df.loc[0, "minutes_played"] == 90
    assert "Goals Scored" not in df.columns
    assert "carries_prgc" not in df.columns
    assert df.loc[0, "season_label"] == "2023-2024"


def test_load_and_clean_csv_rejects_missing_required_columns(tmp_path):
    path = tmp_path / "cleaned_2023-24.csv"
    pd.DataFrame([{"player": "Example"}]).to_csv(path, index=False, encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        load_and_clean_csv(str(path))
