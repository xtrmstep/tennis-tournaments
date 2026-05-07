import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

export const signup = (email, password) =>
  api.post('/auth/signup', { email, password })

export const login = (email, password) =>
  api.post('/auth/login', { email, password })

export const logout = () => api.post('/auth/logout')

export const getMe = () => api.get('/auth/me')

export const getPeople = () => api.get('/people/')

export const createPerson = (formData) =>
  api.post('/people/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const updateRating = (id, rating) =>
  api.put(`/people/${id}/rating`, { rating })

/**
 * Run sorting with the given mode.
 * @param {string} mode - 'singles' or 'doubles'
 * @param {number|undefined} seed - optional RNG seed for reproducible doubles pairing;
 *   not currently exposed in the UI but available for programmatic use
 */
export const runSorting = (mode, seed = undefined) =>
  api.post('/sorting/run', { mode, seed })

export const getSortResult = () => api.get('/sorting/result')
