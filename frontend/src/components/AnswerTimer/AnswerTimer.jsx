import "./AnswerTimer.scss"
import { useEffect, useState, useRef } from "react";


function AnswerTimer({ duration }) {
    const [counter, setCounter] = useState(0);
    const [progressLoaded, setProgressLoaded] = useState(0);
    const intervalRef = useRef();


    useEffect(() => {
        intervalRef.current = setInterval(() => {
            setCounter((cur) => cur + 1);
        }, 1000);
        return () => clearInterval(intervalRef.current)
    }, []);

    useEffect(() => {
        setProgressLoaded(100* (counter / duration));

        if(counter === duration) {
              clearInterval(intervalRef.current);

              setTimeout(() => {
                handleTimeUp();
              }, 1000);
        }
    }, [counter]);

    return <div className="answer-timer-container">
        <div
         style={{
            width: `${progressLoaded}%`,
            backgroundColor: `${
                progressLoaded < 50 ? `lightgreen` : progressLoaded < 70
            }`
         }}
         className="progress">

        </div>
    </div>

}

export default AnswerTimer;