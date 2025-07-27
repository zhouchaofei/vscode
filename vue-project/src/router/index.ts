import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dataScreen'
    },
    {
      path: '/dataScreen',
      name: 'DataScreen',
      component: () => import('@/views/dataScreen/index.vue')
    }
  ]
})

export default router