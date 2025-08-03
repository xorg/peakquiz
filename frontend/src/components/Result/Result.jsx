import "./Result.scss"

const Result = ({questions, result, onTryAgain}) => {
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
            <button onClick={onTryAgain}>Neuer Versuch</button>
        </div>
    );
}

export default Result;