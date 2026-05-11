import { useState } from 'react'
import { api } from './services/api'
import { Navigation } from './components/Navigation'
import { Footer } from './components/Footer'
import { AdminPage } from './pages/AdminPage'
import { LandingPage } from './pages/LandingPage'
import { CategoryPage } from './pages/CategoryPage'
import { QuizPage } from './pages/QuizPage'
import { LeaderboardPage } from './pages/LeaderboardPage'
import { ProfilePage } from './pages/ProfilePage'
import { useAuth } from './hooks/useAuth'

type Route = 'home' | 'categories' | 'quiz' | 'leaderboard' | 'profile' | 'admin'

export default function App() {
  const [route, setRoute] = useState<Route>('home')
  const [quizCategory, setQuizCategory] = useState<string | undefined>(undefined)
  const [quizMode, setQuizMode] = useState<'timed' | 'chill'>('timed')
  const { user, loading, logout } = useAuth()

  const handleLoginClick = () => {
    window.location.href = api.auth.googleLoginUrl()
  }

  const handleCategoryStart = (category: string, mode: 'timed' | 'chill') => {
    setQuizCategory(category)
    setQuizMode(mode)
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
        onAdminClick={() => setRoute('admin')}
      />
      {route === 'home' && <LandingPage onStart={() => setRoute('categories')} />}
      {route === 'categories' && <CategoryPage onStart={handleCategoryStart} />}
      {route === 'quiz' && (
        <QuizPage
          category={quizCategory}
          mode={quizMode}
          onPlayAgain={() => setRoute('categories')}
        />
      )}
      {route === 'leaderboard' && <LeaderboardPage onPlay={() => setRoute('categories')} />}
      {route === 'profile' && <ProfilePage />}
      {route === 'admin' && user?.is_admin && <AdminPage />}
      <Footer />
    </>
  )
}
