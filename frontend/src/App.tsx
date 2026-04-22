import { useState } from 'react'
import { api } from './services/api'
import { Navigation } from './components/Navigation'
import { LandingPage } from './pages/LandingPage'
import { CategoryPage } from './pages/CategoryPage'
import { QuizPage } from './pages/QuizPage'
import { LeaderboardPage } from './pages/LeaderboardPage'
import { ProfilePage } from './pages/ProfilePage'
import { useAuth } from './hooks/useAuth'

type Route = 'home' | 'categories' | 'quiz' | 'leaderboard' | 'profile'

export default function App() {
  const [route, setRoute] = useState<Route>('home')
  const [quizCategory, setQuizCategory] = useState<string | undefined>(undefined)
  const { user, loading, logout } = useAuth()

  const handleLoginClick = () => {
    window.location.href = api.auth.googleLoginUrl()
  }

  const handleCategoryStart = (category: string) => {
    setQuizCategory(category)
    setRoute('quiz')
  }

  if (loading) return null

  return (
    <>
      <Navigation
        user={user}
        onLoginClick={handleLoginClick}
        onLogoutClick={logout}
        onProfileClick={() => setRoute('profile')}
        onHomeClick={() => setRoute('home')}
        onLeaderboardClick={() => setRoute('leaderboard')}
      />
      {route === 'home' && <LandingPage onStart={() => setRoute('categories')} />}
      {route === 'categories' && <CategoryPage onStart={handleCategoryStart} />}
      {route === 'quiz' && (
        <QuizPage
          category={quizCategory}
          onPlayAgain={() => setRoute('categories')}
        />
      )}
      {route === 'leaderboard' && <LeaderboardPage onPlay={() => setRoute('categories')} />}
      {route === 'profile' && <ProfilePage />}
    </>
  )
}
