import Quiz from "./components/Quiz/Quiz";
import { useState, useEffect } from "react";


function App() {
  const [questions, setQuestions] = useState([]);
  useEffect(() => {
    getQuestions();
  }, []);
  const getQuestions = async () => {
    try {
      const protocol = import.meta.env.MODE == "development" ? "http://" : "https://";
      const response = await fetch(protocol + import.meta.env.VITE_BACKEND_HOST + "/api/peaks")
      const questionsResponse = await response.json();
      setQuestions(questionsResponse);
    } catch (error) {
      console.log(error);
    }
  };

  return (questions.length && <Quiz questions={questions} />);
}

export default App;
