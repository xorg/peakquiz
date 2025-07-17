
import random

from django.http import JsonResponse
from peakquiz.models import Peak


def get_random_peak() -> JsonResponse:
    all_peaks = list(Peak.objects.all())

    random_item = random.choice(all_peaks)
