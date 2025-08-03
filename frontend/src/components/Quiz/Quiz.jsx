import { useState } from "react";
import { resultInitialState } from "../../constants";
import AnswerTimer from "../AnswerTimer/AnswerTimer";
import "./Quiz.scss";
import Result from "../Result/Result";

const Quiz = ({ questions }) => {
    const [currentQuestion, setCurrentQuestion] = useState(0);
    const [answerIdx, setAnswerIdx] = useState(null);
    const [answer, setAnswer] = useState(null);
    const [result, setResult] = useState(resultInitialState);
    const [showResult, setShowResult] = useState(false);
    const [showAnswerTimer, setShowAnswerTimer] = useState(true);
    const [inputAnswer, setInputAnswer] = useState('');



    const { question, choices, correctAnswer, type } = questions[currentQuestion];

    const onAnswerClick = (answer, index) => {
        setAnswerIdx(index);
        if (answer == correctAnswer) {
            setAnswer({ correct: true, answerText: answer });
        } else {
            setAnswer({ correct: false, answerText: answer })
        }
    }

    const onClickNext = (finalAnswer) => {
        setAnswerIdx(null);
        setShowAnswerTimer(false);
        setResult((prev) =>
            answer.correct
                ? {
                    ...prev,
                    score: prev.score + 5,
                    correctAnswers: prev.correctAnswers + 1,
                    answersList: [
                        ...prev.answersList, answer
                    ]
                } : {
                    ...prev,
                    wrongAnswers: prev.wrongAnswers + 1,
                    answersList: [
                        ...prev.answersList, answer
                    ]
                });


        if (currentQuestion !== questions.length - 1) {
            setCurrentQuestion((prev) => prev + 1);
        } else {
            setCurrentQuestion(0);
            setShowResult(true);
        }


        setTimeout(() => {
            setShowAnswerTimer(true);
        }, 100);
    }

    const onTryAgain = () => {
        setResult(resultInitialState);
        setShowResult(false);
        window.location.reload();

    }

    const handleTimeUp = () => {
        setAnswer({ correct: false, answerText: '' });
        onClickNext(false);
    }

    const handleInputChange = (event) => {
        setInputAnswer(event.target.value);

        if (event.target.value) {
            setAnswer({ correct: true, answerText: event.target.value });
        } else {
            setAnswer({ correct: false, answerText: event.target.value });
        }
    }

    const getAnswerUI = () => {
        if (type === 'FIB') {
            return <input value={inputAnswer} onChange={handleInputChange} />
        }
        return (
            <ul>
                {
                    choices.map((answer, index) => (
                        <li
                            key={answer}
                            onClick={() => onAnswerClick(answer, index)}
                            className={answerIdx === index ? 'selected-answer' : null}>
                            {answer}
                        </li>
                    ))
                }
            </ul>);
    }

    return (
        <div className="quiz-container">
            {!showResult ? (
                <>
                    {showAnswerTimer && (
                        <AnswerTimer duration={300} onTimeUp={handleTimeUp} />)}
                    <span className="active-question-no">{currentQuestion + 1}</span>
                    <span className="total-questions">/{questions.length}</span>
                    <span className="peak-picture"><img src={question} alt="" width="100%" /></span>
                    {getAnswerUI(type)}
                    <div className="footer">
                        <button onClick={() => onClickNext(answer)} disabled={answerIdx === null && !inputAnswer}>
                            {currentQuestion == questions.length - 1 ? "Fertig" : "Weiter"}
                        </button>
                    </div>
                </>) : (<Result result={result} onTryAgain={onTryAgain} questions={questions} />)}

        </div>
    )
}

export default Quiz;