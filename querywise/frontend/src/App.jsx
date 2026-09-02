import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import QueryAnalyzer from './pages/QueryAnalyzer.jsx'
import QueryHistory from './pages/QueryHistory.jsx'
import IndexRecommendations from './pages/IndexRecommendations.jsx'
import QueryDetails from './pages/QueryDetails.jsx'
import DatabaseExplorer from './pages/DatabaseExplorer.jsx'

export default function App() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 min-w-0">
        <div className="max-w-6xl mx-auto px-4 md:px-8 py-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analyzer" element={<QueryAnalyzer />} />
            <Route path="/history" element={<QueryHistory />} />
            <Route path="/history/:id" element={<QueryDetails />} />
            <Route path="/recommendations" element={<IndexRecommendations />} />
            <Route path="/explorer" element={<DatabaseExplorer />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}
