import { createApp } from 'vue'
import App from './App.vue'
import router from './router/router'
import 'video.js/dist/video-js.css'
import './styles/index.scss'

// 1. 引入 echarts
import * as echarts from "echarts";
import "echarts-liquidfill"; // 引入水球图

const app =  createApp(App);

// 2. 挂载到全局
app.config.globalProperties.$echarts = echarts;

app.use(router)
app.mount('#app')