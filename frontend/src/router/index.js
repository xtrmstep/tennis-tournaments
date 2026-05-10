import { createRouter, createWebHistory } from 'vue-router'
import { getMe } from '../services/api'

const routes = [
  { path: '/', redirect: '/people' },
  { path: '/login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  { path: '/signup', component: () => import('../views/SignUpView.vue'), meta: { public: true } },
  { path: '/profile', component: () => import('../views/ProfileView.vue'), meta: { skipProfileCheck: true } },
  { path: '/people', component: () => import('../views/PeopleView.vue') },
  { path: '/people/new', component: () => import('../views/PersonFormView.vue') },
  { path: '/sorting', component: () => import('../views/SortingView.vue') },
  { path: '/admin/users', component: () => import('../views/AdminUsersView.vue'), meta: { adminOnly: true } },
  { path: '/competitions', component: () => import('../views/CompetitionsView.vue') },
  { path: '/competitions/new', component: () => import('../views/CompetitionFormView.vue'), meta: { moderatorOrAdmin: true } },
  { path: '/competitions/:id', component: () => import('../views/CompetitionView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.public) {
    try {
      const res = await getMe()
      return res.data.profile_complete ? '/people' : '/profile'
    } catch {
      return true
    }
  }
  try {
    const res = await getMe()
    if (to.meta.adminOnly && !res.data.is_admin) {
      return '/people'
    }
    if (to.meta.moderatorOrAdmin && !res.data.is_admin && !res.data.is_moderator) {
      return '/competitions'
    }
    if (!res.data.profile_complete && !to.meta.skipProfileCheck) {
      return '/profile'
    }
    return true
  } catch {
    return { path: '/login', query: { next: to.fullPath } }
  }
})

export default router
