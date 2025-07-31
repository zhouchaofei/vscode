import { createRouter, createWebHistory } from 'vue-router'
import Annotation from '../components/Annotation.vue'
import DataScreen from '../views/DataScreen.vue'
import VideoPlayback from '../views/VideoPlayback.vue'

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
  },
  {
    path: '/videoplayback',
    name: 'VideoPlayback',
    component: VideoPlayback
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router