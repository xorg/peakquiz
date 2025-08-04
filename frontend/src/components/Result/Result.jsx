import "./Result.scss"
import { useState, useEffect } from "react";

const Result = ({ questions, result, onTryAgain }) => {

    const [name, setName] = useState('');
    const [highScores, setHighScores] = useState([]);
    const [showScores, setShowScores] = useState(false);

    useEffect(() => {
        setHighScores(JSON.parse(localStorage.getItem("highScores")) || []);
    }, []);
    /*
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
    */
    const handleSave = () => {
        const score = {
            totalGuesses: questions.length,
            correctGuesses: result.correctAnswers,
            wrongGuesses: result.wrongAnswers,
        };

        const newHighScores = {
                totalGuesses: highScores.totalGuesses + score.totalGuesses,
                correctGuesses: highScores.correctGuesses + score.correctGuesses,
                wrongGuesses: highScores.wrongGuesses + score.wrongGuesses,
                percentage: Math.round(((highScores.correctGuesses + score.correctGuesses) / (highScores.totalGuesses + score.totalGuesses)) * 100)
        };
        setHighScores(newHighScores);
        setShowScores(true);
        localStorage.setItem("highScores", JSON.stringify(newHighScores));
    }

    const handleTryAgain = () => {
        setShowScores(false);
        setHighScores([]);
        onTryAgain();
    }

    return (
        <div className="result">
            <h3>Resultat</h3>
            <p>
                Anzahl Gipfel: <span>{questions.length}</span>
            </p>
            <p>
                Punkte: <span>{result.score}</span>
            </p>
            <p>
                Richtig: <span>{result.correctAnswers}</span>
            </p>
            Antworten:
            <ul>
                {


                    result.answersList.map((x, index) => (

                        <li key={x.answerText} style={{
                            backgroundColor: `${x.correct
                                ? 'lightblue'
                                : 'orange'
                                }`,
                        }}>
                            <a target="_blank" rel="noopener noreferrer" href={questions[index].question}>{x.answerText}</a>
                        </li>
                    ))
                }
            </ul>
            <p>
                Falsch: <span>{result.wrongAnswers}</span>
            </p>
            <button onClick={handleTryAgain}>Neuer Versuch</button>

            {!showScores ? <>
                <button onClick={handleSave} >Statistik</button>
            </> : <>
                <table>
                    <thead>
                        <tr>
                            <th>Anzahl</th>
                            <th>Richtig</th>
                            <th>Falsch</th>
                            <th>Genauigkeit</th>
                        </tr>
                    </thead>
                    <tbody>
                         {
                                 <tr key={`highscores`}>
                                    <td>{highScores.totalGuesses}</td>
                                    <td>{highScores.correctGuesses}</td>
                                    <td>{highScores.wrongGuesses}</td>
                                    <td>{highScores.percentage}%</td>
                                </tr>
                        }
                    </tbody>
                </table>

            </>}
            {

            }
        </div>
    );
}

export default Result;