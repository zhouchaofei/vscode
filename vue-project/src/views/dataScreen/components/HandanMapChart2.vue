<template>
  <div class="map-container">
    <div ref="chartRef" class="echarts-map"></div>
    <div v-if="showVideoPopup" class="video-popup" :style="videoPopupStyle">
      <div class="popup-header">
        <span class="popup-title">{{ currentCamera.name }} - 实时监控</span>
        <span class="popup-close" @click="closeVideoPopup">×</span>
      </div>
      <div class="popup-content">
        <div v-if="videoLoading" class="video-loading">正在加载视频流...</div>
        <div id="video-popup-container" class="video-js-container"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from "vue";
import * as echarts from "echarts";
import handanMapJson from "../assets/yn_and_feixiang.json";
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
// import 'videojs-contrib-hls'; // **关键：导入HLS插件**
import '@videojs/http-streaming'; // 新的、兼容 Vite 的插件

// --- ECharts 地图实例和DOM引用 ---
const chartRef = ref<HTMLDivElement>();
let myChart: echarts.ECharts;
let resizeObserver: ResizeObserver; // **新增：用于监听尺寸变化**

// --- 视频弹窗状态 ---
const showVideoPopup = ref(false);
const videoPopupStyle = ref({});
const currentCamera = ref<any>({});
const videoLoading = ref(false); // **新增：用于显示加载状态**
let player: videojs.Player | null = null;

// --- 萤石云 API 配置 (从 DataScreen.vue 迁移) ---
const appKey = 'd4baaab8baf24baa9541f1bbe64b2200';
const appSecret = 'f42fb82edaed28c57b2045d882f0208e';

// --- 摄像头数据 (增加了 deviceSerial) ---
const cameraData = ref([
    { name: "永年", value: [114.55, 36.80], deviceSerial: '33011063992677425735:33010516991327760034' },
    { name: "肥乡北", value: [114.80, 36.65], deviceSerial: '33011063992677425735:33010084991327588111' },
    { name: "肥乡南", value: [114.85, 36.55], deviceSerial: '33011063992677425735:33011012991327147072' },
    { name: "肥乡梁厂", value: [114.90, 36.60], deviceSerial: '33011063992677425735:33011033991327056374' }
]);

// --- 摄像头图标 (SVG Path) ---
const cameraIcon = 'path://M14.6,12.5H9.4c-1.2,0-2.1-0.9-2.1-2.1V5.1c0-1.2,0.9-2.1,2.1-2.1h5.3c1.2,0,2.1,0.9,2.1,2.1v5.3C16.7,11.6,15.8,12.5,14.6,12.5z M9.4,4.1c-0.6,0-1.1,0.5-1.1,1.1v5.3c0,0.6,0.5,1.1,1.1,1.1h5.3c0.6,0,1.1-0.5,1.1-1.1V5.1c0-0.6-0.5-1.1-1.1-1.1H9.4z M17.9,16.8H6.1c-1.2,0-2.1-0.9-2.1-2.1V7.4h1.1v7.3c0,0.6,0.5,1.1,1.1,1.1h11.8c0.6,0,1.1-0.5,1.1-1.1V7.4h1.1v7.3C20,15.9,19.1,16.8,17.9,16.8z M12,14.6c-0.6,0-1-0.4-1-1v-2.1c0-0.6,0.4-1,1-1s1,0.4,1,1v2.1C13,14.2,12.6,14.6,12,14.6z';

// --- ECharts 配置 ---
const option: any = { // 使用 'any' 类型来绕过本地不完整的 ECOption 类型定义
  tooltip: {
    trigger: 'item',
    formatter: (params: any) => {
      if (params.seriesName === '摄像头') {
        return params.name;
      }
      return ''; // 地图区域不显示 tooltip
    }
  },
  geo: {
    map: "handan",
    zoom: 1.1,
    center: [114.65, 36.72],
    roam: true,
    itemStyle: { // 地图区域的默认样式
      areaColor: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: '#073684' }, { offset: 1, color: '#061E3D' }]
      },
      borderColor: '#2B91B7',
      borderWidth: 1,
    },
    emphasis: { disabled: true }, // 禁用鼠标划过和选中的高亮效果
    select: { disabled: true }
  },
  series: [
    {
      name: "摄像头",
      type: "effectScatter",
      coordinateSystem: "geo",
      data: cameraData.value,
      symbol: cameraIcon,
      symbolSize: 20,
      zlevel: 10,
      itemStyle: { color: '#00d0ff' },
      label: { show: true, position: 'bottom', formatter: '{b}', color: '#fff', fontSize: 12 },
      emphasis: { scale: 1.5 },
      rippleEffect: { brushType: 'stroke', scale: 3 }
    },
  ],
};

// --- ECharts 初始化和事件绑定 ---
const initChart = () => {
  if (!chartRef.value) return;
  myChart = echarts.init(chartRef.value);
  echarts.registerMap("handan", handanMapJson as any);
  myChart.setOption(option);

  myChart.on('click', async (params) => {
    if (params.seriesName === '摄像头' && !showVideoPopup.value) {
      const camera = params.data as any;
      const pointInPixel = myChart.convertToPixel('geo', camera.value);
      
      currentCamera.value = camera;
      videoPopupStyle.value = { left: `${pointInPixel[0]}px`, top: `${pointInPixel[1]}px` };
      showVideoPopup.value = true;
      videoLoading.value = true;
      
      await nextTick();
      await playVideo(camera);
    }
  });
};

// --- 视频播放逻辑 ---

/**
 * 获取一个有效的萤石云 accessToken，优先从缓存读取。
 */
const getValidAccessToken = async () => {
  const tokenInfo = JSON.parse(localStorage.getItem('ys7TokenInfo') || 'null');

  if (tokenInfo && tokenInfo.accessToken && tokenInfo.expireTime > Date.now()) {
    return tokenInfo.accessToken;
  }
  
  const url = 'https://open.ys7.com/api/lapp/token/get';
  const params = new URLSearchParams();
  params.append('appKey', appKey); //
  params.append('appSecret', appSecret); //

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params
    });
    const data = await response.json();

    if (data.code === '200') {
      const { accessToken, expireTime } = data.data;
      localStorage.setItem('ys7TokenInfo', JSON.stringify({ accessToken, expireTime }));
      return accessToken;
    } else {
      throw new Error(`获取萤石AccessToken失败: ${data.msg}`);
    }
  } catch (error) {
    console.error("获取AccessToken时出错:", error);
    throw error;
  }
};

/**
 * 使用 accessToken 获取指定摄像头的HLS直播地址。
 */
const fetchCameraUrl = async (token: string, camera: any) => {
  const url = 'https://open.ys7.com/api/lapp/v2/live/address/get';
  const params = new URLSearchParams();
  params.append('accessToken', token);
  params.append('deviceSerial', camera.deviceSerial); //
  params.append('channelNo', '1');
  params.append('protocol', '2'); // 1-hls, 2-http-hls

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params
    });
    const data = await response.json();
    if (data.code === '200' && data.data) {
      return data.data.url;
    } else {
      throw new Error(`获取 ${camera.name} 视频流地址失败: ${data.msg}`);
    }
  } catch(error) {
    console.error(`获取视频流地址时出错:`, error);
    throw error;
  }
};

/**
 * 组合获取令牌和视频地址的流程，并初始化播放器。
 */
const playVideo = async (camera: any) => {
  try {
    const token = await getValidAccessToken();
    const videoUrl = await fetchCameraUrl(token, camera);
    videoLoading.value = false;
    await nextTick();
    initVideoPlayer(videoUrl);
  } catch (error) {
    videoLoading.value = false;
    const errorMessage = error instanceof Error ? error.message : "播放视频时发生未知错误";
    alert(errorMessage);
    console.error(errorMessage);
    closeVideoPopup(); // 如果出错则关闭弹窗
  }
};

/**
 * 初始化 Video.js 播放器。
 */
const initVideoPlayer = (url: string) => {
  // 先销毁已存在的播放器实例，防止冲突
  if (player) {
    player.dispose();
    player = null;
  }
  
  const videoOptions: videojs.PlayerOptions = {
    autoplay: true,
    muted: true, // 浏览器通常要求自动播放的视频是静音的
    controls: false,
    preload: 'auto',
    fluid: true,
    sources: [{ src: url, type: 'application/x-mpegURL' }]
  };

  const videoContainer = document.getElementById('video-popup-container');
  if (videoContainer) {
    // 清空容器并创建新的 video 元素
    videoContainer.innerHTML = `<video class="video-js vjs-default-skin"></video>`;
    const videoElement = videoContainer.querySelector('video');
    
    if (videoElement) {
        player = videojs(videoElement, videoOptions, () => {
          console.log('播放器准备就绪');
          player?.play();
        });
    }
  }
};

/**
 * 关闭视频弹窗并销毁播放器。
 */
const closeVideoPopup = () => {
  showVideoPopup.value = false;
  if (player) {
    player.dispose();
    player = null;
  }
};

// --- Vue 生命周期钩子 ---
onMounted(() => {
  // **关键修改：使用 nextTick 确保 DOM 渲染完成**
  nextTick(() => {
    initChart();
    // **关键修改：监听容器尺寸变化**
    if (chartRef.value) {
      resizeObserver = new ResizeObserver(() => {
        myChart?.resize();
      });
      resizeObserver.observe(chartRef.value);
    }
  });
});

onBeforeUnmount(() => {
  closeVideoPopup(); // 组件卸载前确保关闭弹窗和播放器
  if (myChart) {
    myChart.dispose();
  }
  // **关键修改：停止监听**
  if (resizeObserver && chartRef.value) {
    resizeObserver.unobserve(chartRef.value);
  }
});
</script>


<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.echarts-map {
  width: 100%;
  height: 100%;
}

.video-popup {
  position: absolute;
  width: 480px;
  height: 320px;
  background-color: #0c2049;
  border: 1px solid #4db6e5;
  border-radius: 8px;
  box-shadow: 0 0 20px rgba(0, 208, 255, 0.5);
  z-index: 100;
  display: flex;
  flex-direction: column;
  transform: translate(-50%, -110%);
}
.video-popup::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-top: 10px solid #4db6e5;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: rgba(77, 182, 229, 0.2);
  color: #fff;
  font-size: 14px;
}

.popup-close {
  cursor: pointer;
  font-size: 20px;
  font-weight: bold;
}
.popup-close:hover {
  color: #ff5733;
}

.popup-content {
  flex-grow: 1;
  background-color: #000;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
}

.video-js-container {
  width: 100%;
  height: 100%;
}

.video-loading {
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}
</style>