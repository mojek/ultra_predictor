import logging
from celery import chain, group, chord
from config import celery_app
from django.db import transaction
from .models import PredictionRace, PredictionRaceGroup
from .extras.itra_result_fetcher import ItraRaceResultFetcher
from .extras.itra_runner_birth_fetcher import ItraRunnerBirthFetcher
from .extras.itra_result_parser import ItraRaceResultsParser, ItraRunnerProfileParser
from .extras.enduhub_fetcher import EnduhubFetcher
from .extras.enduhub_parser import EnduhubParser
from .models import PredictionRaceResult, Runner, HistoricalRaceResult, HistoricalRace
from ultra_predictor.csv_generator.extras.csv_generator import CsvGenerator

logger = logging.getLogger(__name__)


@celery_app.task
def process_itra_download(race_id):
    """First task download results from itra page with one shot
       then every result fire new task to download year of birth.
    """
    chain_process = chain(
        fetch_result_data_from_itra.s(race_id), group_itra_year_fetcher_task.s()
    )
    return chain_process


@celery_app.task
def group_itra_year_fetcher_task(results):
    return group(
        fetch_year_and_save_results.s(result, results["race_id"])
        for result in results["results"]
    )()


@celery_app.task()
def process_endu_download(race_id):
    prediction_race = PredictionRace.objects.get(pk=race_id)
    return group(
        fetch_enduhub_runner_download.s(runner.id)
        for runner in prediction_race.runners.all()
    )()

@celery_app.task()
def process_csv_files(group_id):
    prediction_race_group = PredictionRaceGroup.objects.get(pk=group_id)
    CsvGenerator(group=prediction_race_group)

@celery_app.task()
def process_csv_file_for_all():
    CsvGenerator()



@celery_app.task(bind=True, default_retry_delay=60, max_retries=120)
def fetch_result_data_from_itra(self, race_id):
    """Download  race results from itra page"""
    prediction_race = PredictionRace.objects.get(pk=race_id)
    itra_fetcher = ItraRaceResultFetcher(itra_race_id=prediction_race.itra_race_id)
    itra_parser = ItraRaceResultsParser(itra_fetcher.get_data())
    return {
        "results": [result.to_dict() for result in itra_parser.race_results],
        "race_id": race_id,
    }


@celery_app.task(bind=True, default_retry_delay=60, max_retries=120)
def fetch_year_and_save_results(self, result, race_id):
    """Find year on Itra Page and save runner and race results"""

    prediction_race = PredictionRace.objects.get(pk=race_id)
    itra_birth = ItraRunnerBirthFetcher(
        first_name=result["first_name"], last_name=result["last_name"]
    )
    itra_parser = ItraRunnerProfileParser(itra_birth.get_data())
    with transaction.atomic():
        runner, runner_created = Runner.objects.get_or_create(
            first_name=result["first_name"],
            last_name=result["last_name"],
            sex=result["sex"],
            nationality=result["nationality"],
            birth_year=itra_parser.birth_year,
        )
        result, result_created = PredictionRaceResult.objects.get_or_create(
            runner=runner,
            prediction_race=prediction_race,
            time_result=result["time_result"],
            position=result["position"],
        )
        logger.info(
            "{} Runner: {}".format(
                "Added:" if runner_created else "already exists:", runner
            )
        )
        logger.info(
            "{} PredictionRaceResult: {}".format(
                "Added:" if result_created else "already exists:", result
            )
        )

    return "ok"


@celery_app.task(bind=True, default_retry_delay=60, max_retries=120)
def fetch_enduhub_runner_download(self, runner_id):
    runner = Runner.objects.get(pk=runner_id)
    page = 1
    all_results = []
    while True:
        endu_fetcher = EnduhubFetcher(runner.name, page)
        endu_parser = EnduhubParser(endu_fetcher.get_data(), runner.birth_year)
        all_results += endu_parser.results()

        if endu_parser.has_next_page:
            page += 1
        else:
            break

    for result in all_results:
        with transaction.atomic():
            historical_race, race_created = HistoricalRace.objects.get_or_create(
                name=result["race_name"],
                start_date=result["start_date"],
                distance=result["distance"],
                race_type=result["race_type"],
            )

            logger.info(
                "{} HistoricalRace: {}".format(
                    "Added:" if race_created else "already exists:", historical_race
                )
            )

            hist_result, result_created = HistoricalRaceResult.objects.get_or_create(
                runner=runner,
                historical_race=historical_race,
                time_result=result["time_result"],
            )
            logger.info(
                "{} HistoricalRaceResult: {}".format(
                    "Added:" if result_created else "already exists:", hist_result
                )
            )

    return "ok"

