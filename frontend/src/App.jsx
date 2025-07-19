import Quiz from "./components/Quiz/Quiz";
import { useState, useEffect } from "react";


function App() {
  const [questions, setQuestions] = useState([]);
  useEffect(() => {
    getQuestions();
  }, []);

  const getQuestions = async () => {
    try {
      const response = await fetch("http://192.168.0.149:8000/api/peaks")
      const questionsResponse = await response.json();
      setQuestions(questionsResponse);
    } catch (error) {
      console.log(error);
    }
  };

  return (questions.length && <Quiz questions={questions} />);
}

export default App;
