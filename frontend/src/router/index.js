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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  try {
    const res = await getMe()
    if (!res.data.profile_complete && !to.meta.skipProfileCheck) {
      return '/profile'
    }
    return true
  } catch {
    return '/login'
  }
})

export default router
