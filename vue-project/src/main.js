import { createApp } from 'vue'
import App from './App.vue'
import router from './router/router'
import 'video.js/dist/video-js.css'
import './styles/index.scss'

createApp(App)
  .use(router)
  .mount('#app')