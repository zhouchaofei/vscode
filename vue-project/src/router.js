import { createRouter, createWebHistory } from 'vue-router'
import DataScreen from './DataScreen.vue'
import Annotation from './components/Annotation.vue'

const routes = [
  {
    path: '/',
    name: 'DataScreen',
    component: DataScreen
  },
  {
    path: '/annotation',
    name: 'Annotation',
    component: Annotation
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router