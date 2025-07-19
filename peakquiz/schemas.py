from ninja import Schema


class Question(Schema):
    """
    Expected output
    question: "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/DammastockFromN.jpg/2560px-DammastockFromN.jpg",
      type: "FIB",
      correctAnswer: "Dammastock",
    """
    question: str
    type: str
    correctAnswer: str

class QuestionList(Schema):
    questions: list[Question]
