import { createRouter, createWebHistory } from 'vue-router'
import { getMe } from '../services/api'

const routes = [
  { path: '/', redirect: '/people' },
  { path: '/login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  { path: '/signup', component: () => import('../views/SignUpView.vue'), meta: { public: true } },
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
    await getMe()
    return true
  } catch {
    return '/login'
  }
})

export default router
