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

    // Category picker
    categoryTitle: 'Choose your challenge',
    categorySubtitle: 'Select a region or test yourself on all Swiss peaks',
    categoryStartBtn: 'Start Climb',
    categoryAllPeaks: 'Schweizer Berge',
    categoryPeaks: 'peaks',

    // Quiz — idle
    quizIdleTitle: 'Ready to climb?',
    quizIdleDesc: "You'll have 60 seconds to identify as many mountain peaks as possible.",
    quizStart: 'Begin Ascent',

    // Rankings tabs
    rankingsTabAll: 'All peaks',

    // Quiz — active
    quizQuestion: 'WHICH PEAK IS THIS?',
    pts: 'pts',

    // Nickname screen
    nicknameTitle: 'Enter your name for the rankings',
    nicknamePlaceholder: 'Your name',
    nicknameSave: 'Save Name',
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
    favouritePeaksTitle: 'Favourite Peaks',
    favouritePeaksEmpty: 'Answer a peak correctly twice to see it here.',
    correct: 'correct',
    wrong: 'wrong',
    attempts: 'attempts',
    recentGamesTitle: 'Recent Games',
    recentGamesEmpty: 'No games yet — play your first quiz!',
    gameCorrect: 'correct',
    gameWrong: 'wrong',
    breakdownTitle: 'Your answers',
    profileEmptyGuest: 'Play a quiz to create your profile.',
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

    // Category picker
    categoryTitle: 'Wähle deine Herausforderung',
    categorySubtitle: 'Wähle eine Region oder teste dich an allen Schweizer Gipfeln',
    categoryStartBtn: 'Aufstieg starten',
    categoryAllPeaks: 'Schweizer Berge',
    categoryPeaks: 'Gipfel',

    // Quiz — idle
    quizIdleTitle: 'Bereit?',
    quizIdleDesc: 'Du hast 60 Sekunden, um so viele Berggipfel wie möglich zu identifizieren.',
    quizStart: 'Aufstieg beginnen',

    // Rankings tabs
    rankingsTabAll: 'Alle Gipfel',

    // Quiz — active
    quizQuestion: 'WELCHER GIPFEL IST DAS?',
    pts: 'Pkt',

    // Nickname screen
    nicknameTitle: 'Gib deinen Namen für die Rangliste ein',
    nicknamePlaceholder: 'Dein Name',
    nicknameSave: 'Namen speichern',
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
    favouritePeaksTitle: 'Lieblingsgipfel',
    favouritePeaksEmpty: 'Beantworte einen Gipfel zweimal richtig, um ihn hier zu sehen.',
    correct: 'richtig',
    wrong: 'falsch',
    attempts: 'Versuche',
    recentGamesTitle: 'Letzte Spiele',
    recentGamesEmpty: 'Noch keine Spiele — spiel dein erstes Quiz!',
    gameCorrect: 'richtig',
    gameWrong: 'falsch',
    breakdownTitle: 'Deine Antworten',
    profileEmptyGuest: 'Spiele ein Quiz, um dein Profil zu erstellen.',
  },
} as const

export type TranslationKey = keyof typeof translations.en
export type Lang = keyof typeof translations
