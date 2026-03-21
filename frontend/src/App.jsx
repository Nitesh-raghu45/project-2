// frontend/src/App.jsx
import { useState } from 'react'
import { ChatProvider } from './context/ChatContext'
import Sidebar from './components/Sidebar'
import Home from './pages/Home'
import Chat from './pages/Chat'
import RAG from './pages/RAG'
import Research from './pages/Research'
import styles from './App.module.css'

export default function App() {
  const [page, setPage] = useState('home')

  const renderPage = () => {
    switch (page) {
      case 'home':     return <Home onNavigate={setPage} />
      case 'chat':     return <Chat />
      case 'rag':      return <RAG />
      case 'research': return <Research />
      default:         return <Home onNavigate={setPage} />
    }
  }

  return (
    <ChatProvider>
      <div className={styles.layout}>
        <Sidebar page={page} onNavigate={setPage} />
        <main className={styles.main}>
          {renderPage()}
        </main>
      </div>
    </ChatProvider>
  )
}
