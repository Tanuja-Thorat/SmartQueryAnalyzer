import axios from 'axios'

// Base URL for the FastAPI backend. Configurable via .env (VITE_API_URL)
// so the frontend works whether the backend runs locally or in Docker.
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Normalize errors into a simple, user-friendly message so components
// never need to dig into axios/error internals.
function friendlyError(error) {
  if (error.response && error.response.data && error.response.data.detail) {
    return new Error(error.response.data.detail)
  }
  if (error.response && error.response.data && error.response.data.error) {
    return new Error(error.response.data.error)
  }
  if (error.code === 'ECONNABORTED') {
    return new Error('The request took too long. Please try again.')
  }
  if (!error.response) {
    return new Error('Could not reach the QueryWise server. Is the backend running?')
  }
  return new Error('Something went wrong. Please try again.')
}

export async function analyzeQuery(query, runAnalyze = false) {
  try {
    const { data } = await api.post('/api/analyze', { query, run_analyze: runAnalyze })
    return data
  } catch (err) {
    throw friendlyError(err)
  }
}

export async function simulateIndex(query, indexSql) {
  try {
    const { data } = await api.post('/api/simulate-index', { query, index_sql: indexSql })
    return data
  } catch (err) {
    throw friendlyError(err)
  }
}

export async function getHistory({ search = '', slowOnly = false, limit = 50 } = {}) {
  try {
    const { data } = await api.get('/api/history', {
      params: { search: search || undefined, slow_only: slowOnly, limit },
    })
    return data
  } catch (err) {
    throw friendlyError(err)
  }
}

export async function getHistoryDetail(id) {
  try {
    const { data } = await api.get(`/api/history/${id}`)
    return data
  } catch (err) {
    throw friendlyError(err)
  }
}

export async function getDashboard() {
  try {
    const { data } = await api.get('/api/dashboard')
    return data
  } catch (err) {
    throw friendlyError(err)
  }
}

export async function getRecommendations() {
  try {
    const { data } = await api.get('/api/recommendations')
    return data
  } catch (err) {
    throw friendlyError(err)
  }
}

export async function getExplorerTables() {
  try {
    const { data } = await api.get('/api/explorer/tables')
    return data
  } catch (err) {
    throw friendlyError(err)
  }
}

export async function getExplorerTableDetail(tableName) {
  try {
    const { data } = await api.get(`/api/explorer/tables/${tableName}`)
    return data
  } catch (err) {
    throw friendlyError(err)
  }
}

export default api
