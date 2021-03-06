from django.db import models
from django.urls import reverse
from ultra_predictor.core.models import DefaultModel
from django.core.validators import MinValueValidator
from decimal import Decimal
import csv


class Event(DefaultModel):
    name = models.CharField(max_length=255)
    future_event = models.BooleanField(default=False)
    year = models.IntegerField(null=True, blank=True)
    itra_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} {self.year} {self.itra_id} "

    class Meta:
        unique_together = ["name", "year", "itra_id"]


class PredictionRaceGroup(DefaultModel):
    name = models.CharField(max_length=255)

    def get_absolute_url(self):
        return reverse("prediction-group-detailed", kwargs={"pk": self.pk})

    def __str__(self):
        return self.name

    def all_results_of_prediction_races(self):
        return (
            PredictionRaceResult.objects.filter(
                prediction_race__in=self.prediction_races.all()
            )
            .prefetch_related("prediction_race")
            .prefetch_related("runner")
            .order_by("position")
        )


class PredictionRace(DefaultModel):
    UNREADY = "U"
    READY = "R"
    STARTED = "S"
    COMPLETED = "C"
    FAILURE = "F"
    ITRA_DOWNLOAD_STATUSES = (
        (UNREADY, "Unready"),
        (READY, "Ready"),
        (STARTED, "Started"),
        (COMPLETED, "Completed"),
        (FAILURE, "Failure"),
    )

    class Meta:
        unique_together = ["itra_race_id", "race_date"]

    name = models.CharField(max_length=256)
    itra_event_id = models.IntegerField(null=True, blank=True)
    itra_race_id = models.PositiveIntegerField(null=True, blank=True)
    itra_race_event_id = models.PositiveIntegerField(null=True, blank=True)

    race_date = models.DateField(null=True, blank=True)
    race_time = models.TimeField(null=True, blank=True)
    distance = models.DecimalField(max_digits=6, decimal_places=2)
    ascent = models.PositiveIntegerField(null=True, blank=True)
    descent = models.PositiveIntegerField(null=True, blank=True)
    itra_point = models.PositiveIntegerField(null=True, blank=True)
    mount_point = models.PositiveIntegerField(null=True, blank=True)
    finish_point = models.PositiveIntegerField(null=True, blank=True)
    map_link = models.CharField(max_length=256, null=True, blank=True)
    participation = models.CharField(max_length=256, null=True, blank=True)
    refreshment_points = models.PositiveIntegerField(null=True, blank=True)
    sentiers = models.PositiveIntegerField(null=True, blank=True)
    pistes = models.PositiveIntegerField(null=True, blank=True)
    routes = models.PositiveIntegerField(null=True, blank=True)
    challenge = models.CharField(max_length=256, null=True, blank=True)
    championship = models.CharField(max_length=256, null=True, blank=True)
    country_start = models.CharField(max_length=256, null=True, blank=True)
    city_start = models.CharField(max_length=256, null=True, blank=True)
    country_finish = models.CharField(max_length=256, null=True, blank=True)
    city_finish = models.CharField(max_length=256, null=True, blank=True)
    max_time = models.DurationField(null=True, blank=True)
    
    itra_download_status = models.CharField(
        max_length=1, choices=ITRA_DOWNLOAD_STATUSES, default=UNREADY
    )
    runners = models.ManyToManyField(
        "Runner", through="PredictionRaceResult", related_name="prediction_races"
    )

    prediction_race_group = models.ForeignKey(
        PredictionRaceGroup,
        on_delete=models.CASCADE,
        related_name="prediction_races",
        null=True,
        blank=True,
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="prediction_races",
        null=True,
        blank=True,
    )
 
   
    def runners_with_best_count(self, distance):
        results = (
            HistoricalRaceResult.objects.filter(
                runner__in=self.runners.all(),
                historical_race__start_date__lte=self.race_date,
                historical_race__distance=distance,
            )
            .distinct("runner")
            .count()
        )

        return results

    @property
    def month_of_the_race(self):
        return self.race_date.strftime("%B")

    def __str__(self):
        return f"{self.name}"


class HistoricalRace(DefaultModel):
    FLAT = "f"
    MOUNTAIN = "m"
    RACE_TYPE_CHOICES = [(FLAT, "Flat"), (MOUNTAIN, "Mountain")]
    name = models.CharField(max_length=256)
    start_date = models.DateField()
    distance = models.DecimalField(max_digits=6, decimal_places=2)
    race_type = models.CharField(max_length=1, choices=RACE_TYPE_CHOICES, default="o")

    def __str__(self):
        return self.name


class Runner(DefaultModel):
    MAN = "m"
    WOMAN = "w"
    OTHER = "o"
    SEX_CHOICES = [(MAN, "Man"), (WOMAN, "Woman"), (OTHER, "Other")]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_year = models.PositiveSmallIntegerField(validators=[MinValueValidator(1900)])
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, default="o")
    nationality = models.CharField(max_length=100)
    itra_runner_id = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ["first_name", "last_name", "birth_year", "itra_runner_id"]

    def __str__(self):
        return f"{self.name}, {self.birth_year}"

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"


class PredictionRaceResult(DefaultModel):
    runner = models.ForeignKey(
        Runner, on_delete=models.CASCADE, related_name="runners"
    )
    time_result = models.DurationField(null=True, blank=True)
    position = models.PositiveSmallIntegerField(null=True, blank=True)
    prediction_race = models.ForeignKey(
        PredictionRace, on_delete=models.CASCADE, related_name="prediction_race_results"
    )

    @property
    def best_10km_run_before_prediction_race(self):
        return self.runner.historical_race_results.filter(
            historical_race__start_date__lte=self.prediction_race.race_date,
            historical_race__distance=10,
        ).aggregate(models.Min("time_result"))["time_result__min"]

    @property
    def time_result_in_hours(self):
        hours = Decimal(self.time_result.seconds / 3600)
        return round(hours, 2)

    @property
    def runner_age_during_race(self):
        return self.prediction_race.race_date.year - self.runner.birth_year

    def __str__(self):
        return f"{self.runner.name}, {self.prediction_race.name}, {self.time_result}"


class HistoricalRaceResult(DefaultModel):
    runner = models.ForeignKey(
        Runner, on_delete=models.CASCADE, related_name="historical_race_results"
    )
    time_result = models.DurationField()
    historical_race = models.ForeignKey(
        HistoricalRace, on_delete=models.CASCADE, related_name="historical_race_results"
    )

    def __str__(self):
        return f"{self.runner.name}, {self.historical_race.name}, {self.time_result}"

