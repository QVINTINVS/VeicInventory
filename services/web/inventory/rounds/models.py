from enum import auto

import django_rq
from django.core import serializers
from django.db import models

from .storage import NetCDFMinioStorage


class RoundStatus(models.IntegerChoices):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    ERROR = auto()


class WRFRoundManager(models.Manager):
    "TODO: method to schedule / dipatch rounds"

    def send_to_queue(self, emission_instance):
        emission_data = serializers.serialize("json", (emission_instance,))[1:-1]

        queue = django_rq.get_queue("emission_queue")

        queue.enqueue("tasks.process_emission", emission_data)

class RoundsPanel(models.Model):
    pass


class WRFRound(models.Model):
    status = models.IntegerField(
        choices=RoundStatus.choices, default=RoundStatus.PENDING
    )
    timestamp = models.DateTimeField(auto_now=True)
    output_file_path = models.CharField(max_length=255, blank=False)
    namelist = models.JSONField(blank=False)

    netcdf = models.FileField(
        storage=NetCDFMinioStorage(), upload_to="round_outputs/", null=True
    )

    panel = models.ForeignKey(
        RoundsPanel, on_delete=models.CASCADE, related_name="rounds"
    )

    queue = WRFRoundManager()

    def send_to_queue(self):
        """Despacha este round para a fila RQ."""

        emission_data = serializers.serialize("json", (self,))[1:-1]
        queue = django_rq.get_queue("emission_queue")
        queue.enqueue("tasks.process_emission", emission_data)

    def run_if_pending(self):
        if self.status == RoundStatus.PENDING:
            self.status = RoundStatus.RUNNING
            self.save(update_fields="status")

    def complete_if_running(self):
        if self.status == RoundStatus.RUNNING:
            self.status = RoundStatus.COMPLETED
            self.save(update_fields=("status", "timestamp"))
