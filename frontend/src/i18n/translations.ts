export const translations = {
  en: {
    // Landing
    eyebrow: 'THE MOUNTAIN CHALLENGE',
    headline: "How well do you know swiss peaks?",
    tagline: '60 seconds. Mountain photos. How many can you name?',
    heroAlt: 'View from the Zackengrat on Balmhorn into the Valais Alps',
    ctaButton: 'Start the Quiz',
    feature1Title: 'Timed Challenge',
    feature1Desc: '60 seconds to name as many peaks as you can',
    feature2Title: 'Real Photos',
    feature2Desc: 'Identify peaks from stunning mountain photography',
    feature3Title: 'Global Ranking',
    feature3Desc: 'See how you compare to mountain enthusiasts worldwide',

    // Navigation
    signIn: 'Sign in with Google',
    signOut: 'Sign out',

    // Quiz — idle
    quizIdleTitle: 'Ready to climb?',
    quizIdleDesc: "You'll have 60 seconds to identify as many mountain peaks as possible.",
    quizStart: 'Begin Ascent',

    // Quiz — active
    quizQuestion: 'WHICH PEAK IS THIS?',
    pts: 'pts',

    // Nickname screen
    nicknameTitle: 'Enter your name for the rankings',
    nicknamePlaceholder: 'Your name',
    nicknameSave: 'Save Score',
    nicknameSkip: 'Skip',

    // Leaderboard
    yourScore: 'YOUR SCORE',
    playAgain: 'Climb Again',
    globalRankings: 'Rankings',
    loadingRankings: 'Loading rankings…',

    // Profile
    profileTitle: 'Your Stats',
    statTotalGuesses: 'Total Guesses',
    statCorrect: 'Correct',
    statAccuracy: 'Accuracy',
    troublePeaksTitle: 'Peaks to Work On',
    troublePeaksEmpty: 'No trouble spots yet — keep playing!',
    wrong: 'wrong',
    attempts: 'attempts',
    recentGamesTitle: 'Recent Games',
    recentGamesEmpty: 'No games yet — play your first quiz!',
    gameCorrect: 'correct',
    gameWrong: 'wrong',
    breakdownTitle: 'Your answers',
  },
  de: {
    // Landing
    eyebrow: '',
    headline: 'Wie gut kennst du die Gipfel der Schweiz?',
    tagline: '60 Sekunden. Bergfotos. Wie viele kannst du benennen?',
    heroAlt: 'Blick von einem felsigen Alpenvorsprung in ein nebelgefülltes Tal',
    ctaButton: 'Quiz starten',
    feature1Title: 'Zeitwettbewerb',
    feature1Desc: '60 Sekunden, um so viele Gipfel wie möglich zu benennen',
    feature2Title: 'Echte Fotos',
    feature2Desc: 'Erkenne Gipfel anhand beeindruckender Bergfotografie',
    feature3Title: 'Rangliste',
    feature3Desc: 'Vergleiche dich mit anderen Bergbegeisterten',

    // Navigation
    signIn: 'Mit Google anmelden',
    signOut: 'Abmelden',

    // Quiz — idle
    quizIdleTitle: 'Bereit?',
    quizIdleDesc: 'Du hast 60 Sekunden, um so viele Berggipfel wie möglich zu identifizieren.',
    quizStart: 'Aufstieg beginnen',

    // Quiz — active
    quizQuestion: 'WELCHER GIPFEL IST DAS?',
    pts: 'Pkt',

    // Nickname screen
    nicknameTitle: 'Gib deinen Namen für die Rangliste ein',
    nicknamePlaceholder: 'Dein Name',
    nicknameSave: 'Punkte speichern',
    nicknameSkip: 'Überspringen',

    // Leaderboard
    yourScore: 'DEIN ERGEBNIS',
    playAgain: 'Nochmal versuchen',
    globalRankings: 'Rangliste',
    loadingRankings: 'Lade Rangliste…',

    // Profile
    profileTitle: 'Deine Statistiken',
    statTotalGuesses: 'Versuche gesamt',
    statCorrect: 'Richtig',
    statAccuracy: 'Trefferquote',
    troublePeaksTitle: 'Schwierige Gipfel',
    troublePeaksEmpty: 'Noch keine Schwächen — weiterspielen!',
    wrong: 'falsch',
    attempts: 'Versuche',
    recentGamesTitle: 'Letzte Spiele',
    recentGamesEmpty: 'Noch keine Spiele — spiel dein erstes Quiz!',
    gameCorrect: 'richtig',
    gameWrong: 'falsch',
    breakdownTitle: 'Deine Antworten',
  },
} as const

export type TranslationKey = keyof typeof translations.en
export type Lang = keyof typeof translations
