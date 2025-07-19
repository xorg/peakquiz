export const jsQuizz = {
  questions: [
    {
      question:
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/DammastockFromN.jpg/2560px-DammastockFromN.jpg",
      type: "FIB",
      correctAnswer: "Dammastock",
    },
    {
      question:
        "https://upload.wikimedia.org/wikipedia/commons/9/91/Piz_Bernina_Aug_2008_close.jpg",
      choices: [
        "Piz Palü",
        "Piz Bernina",
        "Dufourspitze",
        "Weisshorn",
      ],
      type: "MCQs",
      correctAnswer: "Piz Bernina",
    },
    {
      question: "https://upload.wikimedia.org/wikipedia/commons/4/43/Weisshorn_2.jpg",
      choices: [
        "Dent Blanche",
        "Dent d'Herèns",
        "Matterhorn",
        "Weisshorn",
      ],
      type: "MCQs",
      correctAnswer: "Weisshorn",
    },
    {
      question:
        "https://upload.wikimedia.org/wikipedia/commons/0/0e/Engstligenalp_und_Wildstrubel.jpg",
      choices: ["Wildhorn", "Wildstrubel", "Dents du Midi", "Titlis"],
      type: "MCQs",
      correctAnswer: "Wildstrubel",
    },
    {
      question: "https://upload.wikimedia.org/wikipedia/commons/e/e5/S%C3%A4ntis_-_Batzberg_IMG_9803.JPG",
      choices: ["Säntis", "Rigi", "Stanserhorn", "Titlis"],
      type: "MCQs",
      correctAnswer: "Säntis",
    },
    {
      question: "https://upload.wikimedia.org/wikipedia/commons/1/14/Landscape_Arnisee-region.JPG",
      choices: [
        "Gross Windgällen",
        "Uri Rotstock",
        "Galenstock",
        "Bristen",
      ],
      type: "MCQs",
      correctAnswer: "Gross Windgällen",
    },
  ],
};

export const resultInitialState = {
  score: 0,
  correctAnswers: 0,
  answersList: [],
  wrongAnswers: 0
}