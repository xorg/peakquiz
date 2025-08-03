from ninja import NinjaAPI

import random

from peakquiz.models import Peak, Picture
from peakquiz.schemas import Question


api = NinjaAPI()


@api.get("/peaks")
def get_random_peak(request, number: int = 5) -> list[Question]:
    all_pictures = list(Picture.objects.all())
    all_peak_names = [p.name for p in Peak.objects.all()]

    random_pictures = random.choices(all_pictures, k=number)
    questions = []

    for pic in random_pictures:
        choices = [pic.peak.name]
        random.shuffle(all_peak_names)
        while len(choices) < 4:
            peak_choice = all_peak_names.pop()
            if not peak_choice == pic.peak.name:
                choices.append(peak_choice)
        random.shuffle(choices)
        questions.append(Question(question=pic.cdn_url if pic.cdn_url else pic.original_url, type="MCQ", choices=choices, correctAnswer=pic.peak.name))

    return questions