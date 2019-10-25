# from ultra_predictor.races.models import PredictionRaceGroup


def test_runner_string(db, runner):
    name = runner.name
    birth_year = runner.birth_year
    assert str(runner) == f"{name}, {birth_year}"


def test_race_group_string(db, prediction_race_group):
    assert str(prediction_race_group) == prediction_race_group.name


def test_prediction_race_string(db, prediction_race):
    name = prediction_race.name
    assert str(prediction_race) == name


def test_prediction_race_results_string(db, prediction_race_result):
    assert (
        str(prediction_race_result) == f"{prediction_race_result.runner.name}, "
        f"{prediction_race_result.prediction_race.name}, "
        f"{prediction_race_result.time_result}"
    )


def test_historiacal_race_string(db, historical_race):
    name = historical_race.name
    assert str(historical_race) == name


def test_historical_race_results_string(db, historical_race_result):
    assert (
        str(historical_race_result) == f"{historical_race_result.runner.first_name} "
        f"{historical_race_result.runner.last_name}, "
        f"{historical_race_result.historical_race.name}, "
        f"{historical_race_result.time_result}"
    )
