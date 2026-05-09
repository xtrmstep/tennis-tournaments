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

export const updateProfile = (data) => api.put('/auth/profile', data)

export const getPeople = () => api.get('/people/')

export const getUsers = () => api.get('/users/')

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

export const adminListUsers = () => api.get('/admin/users')

export const adminPatchUser = (id, data) => api.patch(`/admin/users/${id}`, data)

export const adminUpdateUserSkill = (id, skillLevel) =>
  api.patch(`/admin/users/${id}/skill`, { skill_level: skillLevel })

export const adminUpdateUserProfile = (id, data) => api.put(`/admin/users/${id}/profile`, data)

export const adminDeleteUser = (id) => api.delete(`/admin/users/${id}`)

// Competitions
export const getCompetitions = () => api.get('/competitions/')

export const createCompetition = (data) => api.post('/competitions/', data)

export const getCompetition = (id) => api.get(`/competitions/${id}`)

export const updateCompetition = (id, data) => api.put(`/competitions/${id}`, data)

export const transitionCompetition = (id, status) =>
  api.post(`/competitions/${id}/transition`, { status })

export const getCompetitionPlayers = (id) => api.get(`/competitions/${id}/players`)

export const applyToCompetition = (id) => api.post(`/competitions/${id}/apply`)

export const withdrawFromCompetition = (id) => api.delete(`/competitions/${id}/apply`)

export const updatePlayerStatus = (competitionId, playerId, status) =>
  api.patch(`/competitions/${competitionId}/players/${playerId}`, { status })

export const removePlayer = (competitionId, playerId) =>
  api.delete(`/competitions/${competitionId}/players/${playerId}`)

export const getCompetitionMatches = (id) => api.get(`/competitions/${id}/matches`)

export const createMatch = (competitionId, playerAId, playerBId) =>
  api.post(`/competitions/${competitionId}/matches`, {
    player_a_id: playerAId,
    player_b_id: playerBId,
  })

export const setMatchScore = (competitionId, matchId, scoreA, scoreB) =>
  api.patch(`/competitions/${competitionId}/matches/${matchId}/score`, {
    score_a: scoreA,
    score_b: scoreB,
  })

// Competition pairs (doubles grouping)
export const getCompetitionPairs = (id) => api.get(`/competitions/${id}/pairs`)

export const createPair = (competitionId, playerAId, playerBId, teamName) =>
  api.post(`/competitions/${competitionId}/pairs`, {
    player_a_id: playerAId,
    player_b_id: playerBId,
    ...(teamName ? { team_name: teamName } : {}),
  })

export const deletePair = (competitionId, pairId) =>
  api.delete(`/competitions/${competitionId}/pairs/${pairId}`)
