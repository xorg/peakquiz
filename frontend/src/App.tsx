import { useState } from 'react'
import { Navigation } from './components/Navigation'
import { LandingPage } from './pages/LandingPage'
import { QuizPage } from './pages/QuizPage'
import { LeaderboardPage } from './pages/LeaderboardPage'
import { ProfilePage } from './pages/ProfilePage'
import { useAuth } from './hooks/useAuth'

type Route = 'home' | 'quiz' | 'leaderboard' | 'profile'

export default function App() {
  const [route, setRoute] = useState<Route>('home')
  const { user, loading, logout } = useAuth()

  const handleLoginClick = () => {
    window.location.href = '/api/auth/google/login'
  }

  if (loading) return null

  return (
    <>
      <Navigation
        user={user}
        onLoginClick={handleLoginClick}
        onLogoutClick={logout}
        onProfileClick={() => setRoute('profile')}
      />
      {route === 'home' && <LandingPage onStart={() => setRoute('quiz')} />}
      {route === 'quiz' && <QuizPage />}
      {route === 'leaderboard' && <LeaderboardPage />}
      {route === 'profile' && <ProfilePage />}
    </>
  )
}
