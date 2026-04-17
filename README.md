# Peakquiz

THE Quiz app for mountain enthusiasts! Find out how strong your mountain memory is by taking on the ultimate mountain quiz challenge.

Peakquiz is a quiz app that allows users to participate in a timed quiz where they can try to name as many mountain peaks as they can.

# Technical stack
The frontend is written in Typescript and uses React and Vite+. The goal is to have a mobile-first web app that allows the users to experience the quiz in multiple screen sizes

The backend consists of a simple python server that uses FastAPI and a SQLite database to store user data. Authentication uses OAUTH Google login so that users can log in to the app and save their rankings. The database only saves the username and the rank, no other user information is storesd

# UI

The UI design, color schemes and different screens are defined on Stitch. Connect to Stich using the provided MCP config and API Key.

# Features
The app should have following features
- Landing page
  - Landing page with a hero picture, short tag line and a button to start the quiz
  - Quiz
    - The Quiz should be timed 
    - The Quiz shows the user a picture and 4 possible answers
    - For each correct answer the user gets points
    - If the answer is wrong, it does not show the correct answer but let's the user know that that answer is wrong
    - After the time is up a ranking screen is shown with the score of the user. There the user can also see the global ranking
    - In the ranking screen the user can also try the quiz again
  