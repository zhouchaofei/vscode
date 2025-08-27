<template>
  <div class="map-container">
    <div ref="chartRef" class="echarts-map"></div>

    <svg class="line-overlay">
      <line
        v-for="line in lines"
        :key="line.id"
        :x1="line.x1"
        :y1="line.y1"
        :x2="line.x2"
        :y2="line.y2"
        stroke="#4db6e5"
        stroke-width="1.5"
        stroke-dasharray="5, 5"
      />
    </svg>

    <div
      v-for="popup in activePopups"
      :key="popup.camera.deviceSerial"
      ref="popupRefs"
      class="video-popup"
      :style="popup.style"
      @click="handlePopupClick(popup.camera)"
    >
      <div class="popup-header">
        <span class="popup-title">{{ popup.camera.name }}</span>
      </div>
      <div class="popup-content">
        <div v-if="popup.loading" class="video-loading">加载中...</div>
        <div v-if="popup.errorMsg" class="video-loading">{{ popup.errorMsg }}</div>
        <div :id="`video-container-${popup.camera.english}`" class="video-js-container"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from "vue";
import * as echarts from "echarts";
import handanMapJson from "../assets/yn_and_feixiang.json";
import EZUIKit from "ezuikit-js";

const chartRef = ref<HTMLDivElement>();
let myChart: echarts.ECharts;
let resizeObserver: ResizeObserver;
const popupRefs = ref<HTMLDivElement[]>([]);

const activePopups = ref<any[]>([]);
const players = new Map<string, any>(); // Storing EZUIKit player instances
const lines = ref<any[]>([]);

// --- 为播放器添加重试逻辑 ---
const playerMaxRetries = 3; // 每个播放器的最大重试次数
const playerRetryDelay = 5000; // 重试间隔 (5秒)

const appKey = 'd4baaab8baf24baa9541f1bbe64b2200';
const appSecret = 'f42fb82edaed28c57b2045d882f0208e';

const cameraData = ref([
    { id: 1, name: '永年', english: 'yn', deviceSerial: '33011063992677425735:33010516991327760034', view: 'view1', value: [114.5569, 36.7897] },
    { id: 2, name: '肥乡北', english: 'fx_n', deviceSerial: '33011063992677425735:33010084991327588111', view: 'view1', value: [114.7002, 36.5716] },
    { id: 3, name: '肥乡南', english: 'fx_s', deviceSerial: '33011063992677425735:33011012991327147072', view: 'view1', value: [114.7002, 36.5716] },
    { id: 4, name: '肥乡梁场', english: 'fx_lc', deviceSerial: '33011063992677425735:33011033991327056374', view: 'view1', value: [114.7002, 36.5716] }
]);

const cameraIcon = 'path://M14.6,12.5H9.4c-1.2,0-2.1-0.9-2.1-2.1V5.1c0-1.2,0.9-2.1,2.1-2.1h5.3c1.2,0,2.1,0.9,2.1,2.1v5.3C16.7,11.6,15.8,12.5,14.6,12.5z M9.4,4.1c-0.6,0-1.1,0.5-1.1,1.1v5.3c0,0.6,0.5,1.1,1.1,1.1h5.3c0.6,0,1.1-0.5,1.1-1.1V5.1c0-0.6-0.5-1.1-1.1-1.1H9.4z M17.9,16.8H6.1c-1.2,0-2.1-0.9-2.1-2.1V7.4h1.1v7.3c0,0.6,0.5,1.1,1.1,1.1h11.8c0.6,0,1.1-0.5,1.1-1.1V7.4h1.1v7.3C20,15.9,19.1,16.8,17.9,16.8z M12,14.6c-0.6,0-1-0.4-1-1v-2.1c0-0.6,0.4-1,1-1s1,0.4,1,1v2.1C13,14.2,12.6,14.6,12,14.6z';

const option: any = {
  tooltip: {
    trigger: 'item',
    formatter: (params: any) => {
      if (params.seriesName === '摄像头') {
        return params.name;
      }
      return '';
    }
  },
  geo: {
    map: "handan",
    zoom: 1.15,
    center: [114.74, 36.72],
    roam: false,
    itemStyle: {
      areaColor: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: '#073684' }, { offset: 1, color: '#061E3D' }]
      },
      borderColor: '#2B91B7',
      borderWidth: 1,
    },
    label: {
      show: true,       // 显示标签
      color: '#ffffff', // 标签文字颜色
      fontSize: 14,     // 字体大小
    },
    emphasis: { disabled: true },
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
      label: { show: false, position: 'bottom', formatter: '{b}', color: '#fff', fontSize: 12 },
      emphasis: { scale: 1.5 },
      rippleEffect: { brushType: 'stroke', scale: 3 }
    },
  ],
};

const getPopupTransform = (cameraName: string) => {
  switch (cameraName) {
    case '永年': return 'translate(20%, -110%)';
    case '肥乡北': return 'translate(70%, -163%)';
    case '肥乡梁场': return 'translate(70%, -26%)';
    case '肥乡南': return 'translate(-136%, -70%)';
    default: return 'translate(-50%, -120%)';
  }
};

const updateLines = () => {
  if (!myChart || activePopups.value.length === 0 || !chartRef.value) {
    lines.value = [];
    return;
  }

  const newLines = activePopups.value.map((popup, index) => {
    const iconPoint = myChart.convertToPixel('geo', popup.camera.value);
    const popupEl = popupRefs.value[index];

    if (!popupEl || !iconPoint) return null;

    // 获取弹窗未经 transform 时的真实宽高
    const popupWidth = popupEl.offsetWidth;
    const popupHeight = popupEl.offsetHeight;

    // 弹窗的定位基点
    const popupBaseLeft = parseFloat(popupEl.style.left || '0');
    const popupBaseTop = parseFloat(popupEl.style.top || '0');
    
    // 解析 transform 百分比，计算像素偏移量
    const transform = getPopupTransform(popup.camera.name);
    const match = /translate\(([^,]+),([^)]+)\)/.exec(transform);
    let offsetX = 0;
    let offsetY = 0;
    if (match) {
        const tx = match[1].trim();
        const ty = match[2].trim();
        if (tx.endsWith('%')) offsetX = (parseFloat(tx) / 100) * popupWidth;
        if (ty.endsWith('%')) offsetY = (parseFloat(ty) / 100) * popupHeight;
    }

    // 计算出弹窗变换后的、精确的视觉边界
    const visualLeft = popupBaseLeft + offsetX;
    const visualTop = popupBaseTop + offsetY;
    const visualRight = visualLeft + popupWidth;
    const visualBottom = visualTop + popupHeight;

    // 找出图标相对于弹窗视觉边界的最近点
    const closestX = Math.max(visualLeft, Math.min(iconPoint[0], visualRight));
    const closestY = Math.max(visualTop, Math.min(iconPoint[1], visualBottom));

    return {
      id: popup.camera.deviceSerial,
      x1: iconPoint[0],
      y1: iconPoint[1],
      x2: closestX,
      y2: closestY,
    };
  }).filter(Boolean);

  lines.value = newLines as any;
};

const initChart = () => {
  if (!chartRef.value) return;
  myChart = echarts.init(chartRef.value);
  echarts.registerMap("handan", handanMapJson as any);
  myChart.setOption(option);
  myChart.on('geoRoam', updateLines);
};

const openAllPopups = async () => {
  if (!myChart) return;
  
  try {
    const token = await getValidAccessToken();
    
    for (const camera of cameraData.value) {
      const pointInPixel = myChart.convertToPixel('geo', camera.value);
      const style = {
        left: `${pointInPixel[0]}px`,
        top: `${pointInPixel[1]}px`,
        transform: getPopupTransform(camera.name),
      };
      const popup = { camera, style, loading: true, errorMsg: '', retryCount: 0 };
      activePopups.value.push(popup);

      nextTick(() => {
        initVideoPlayer(camera, token);
      });
    }

  } catch (error) {
    alert("初始化摄像头失败，请检查网络或API配置。");
    console.error(error);
  }
};

const handlePopupClick = (camera: any) => {
  const tokenInfo = JSON.parse(localStorage.getItem('ys7TokenInfo') || 'null');
  if (!tokenInfo || !tokenInfo.accessToken) {
    alert("无法获取有效的 Access Token，请刷新页面后重试。");
    return;
  }
  
  const url = `/annotation?accessToken=${tokenInfo.accessToken}&cameraName=${encodeURIComponent(camera.english)}&view=${camera.view}`;
  window.open(url, '_blank');
};

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

const initVideoPlayer = (camera: any, token: string) => {
  const playerId = camera.english;
  if (players.has(playerId)) {
    players.get(playerId)?.destroy();
  }

  const popup = activePopups.value.find(p => p.camera.deviceSerial === camera.deviceSerial);
  const videoContainer = document.getElementById(`video-container-${playerId}`);

  if (!videoContainer) {
    console.error(`Video container for ${camera.name} not found.`);
    if (popup) {
      popup.loading = false;
      popup.errorMsg = '容器不存在';
    }
    return;
  }

  const ezopenURL = `ezopen://open.ys7.com/${camera.deviceSerial}/1.live`;

  const player = new EZUIKit.EZUIKitPlayer({
    id: `video-container-${playerId}`,
    accessToken: token,
    url: ezopenURL,
    template: 'simple',
    quality: '0',
    autoplay: true,
    muted: true,
    audio: false,
    handleSuccess: () => {
      console.log(`${camera.name} 播放成功。`);
      if (popup) {
        popup.loading = false;
        popup.errorMsg = '';
        popup.retryCount = 0; // 播放成功，重置计数器
      }
    },
    handleError: (e: any) => {
      console.error(`${camera.name} 播放错误:`, e);
      if (popup && popup.retryCount < playerMaxRetries) {
        popup.retryCount++;
        popup.errorMsg = `尝试重连... (${popup.retryCount}/${playerMaxRetries})`;
        console.log(`${camera.name} 准备在 ${playerRetryDelay / 1000} 秒后重试...`);
        setTimeout(() => {
          initVideoPlayer(camera, token);
        }, playerRetryDelay);
      } else if (popup) {
        popup.loading = false;
        popup.errorMsg = '重连失败';
        console.error(`${camera.name} 已达到最大重试次数，停止重试。`);
      }
    },
  });
  players.set(playerId, player);
};

watch(activePopups, () => nextTick(updateLines), { deep: true });

onMounted(() => {
  nextTick(() => {
    initChart();
    
    openAllPopups();

    if (chartRef.value) {
      resizeObserver = new ResizeObserver(() => {
        myChart?.resize();
        updateLines();
      });
      resizeObserver.observe(chartRef.value);
    }
  });
});

onBeforeUnmount(() => {
  players.forEach(player => player.destroy());
  players.clear();

  if (myChart) {
    myChart.off('geoRoam', updateLines);
    myChart.dispose();
  }
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
  overflow: hidden;
}

.echarts-map {
  width: 100%;
  height: 100%;
}

.line-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 99;
}

.video-popup {
  position: absolute;
  width: 270px; 
  height: 183px;
  background-color: #0c2049;
  border: 1px solid #4db6e5;
  border-radius: 8px;
  box-shadow: 0 0 20px rgba(0, 208, 255, 0.5);
  z-index: 100;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transform-origin: center center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.video-popup:hover {
  transform: var(--base-transform, translate(-50%, -120%)) scale(1.05);
  box-shadow: 0 0 30px rgba(0, 208, 255, 0.8);
  z-index: 101;
}

.popup-header {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 5px 10px;
  background-color: rgba(77, 182, 229, 0.2);
  color: #fff;
  font-size: 14px;
}

.popup-content {
  flex-grow: 1;
  background-color: #000;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
  position: relative;
}

.video-loading, .video-js-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.video-loading {
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 14px;
  z-index: 2;
  background-color: #000;
}

.video-js-container {
  width: 100%;
  height: 100%;
  z-index: 1;
}
</style>