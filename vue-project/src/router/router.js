import { createRouter, createWebHistory } from 'vue-router'
import Annotation from '../views/Annotation.vue'
import VideoPlayback from '../views/VideoPlayback.vue'

const routes = [
  {
    path: '/annotation',
    name: 'Annotation',
    component: Annotation
  },
  {
    path: '/videoplayback',
    name: 'VideoPlayback',
    component: VideoPlayback
  },
  {
    path: '/',
    name: 'dataScreen',
    component: () => import('@/views/dataScreen/index.vue'),
    meta: {
      title: '互通施工关键流程的智慧管理平台'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router