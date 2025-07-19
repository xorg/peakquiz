from ninja import NinjaAPI

import random

from peakquiz.models import Peak, Picture
from peakquiz.schemas import Question, QuestionList


api = NinjaAPI()


@api.get("/peaks")
def get_random_peak(request, number: int = 5) -> QuestionList:
    all_pictures = list(Picture.objects.all())

    random_pictures = random.choices(all_pictures, k=number)
    questions = []

    for pic in random_pictures:
        questions.append(Question(question=pic.url, type="FIB", correctAnswer=pic.peak.name))

    return QuestionList(questions=questions)