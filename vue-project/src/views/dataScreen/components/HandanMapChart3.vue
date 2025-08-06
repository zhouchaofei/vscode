<template>
  <div class="map-container">
    <!-- ECharts 地图容器 -->
    <div ref="chartRef" class="echarts-map"></div>

    <!-- 用于绘制连接线的 SVG 覆盖层 -->
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

    <!-- 视频弹窗 -->
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
        <div :id="`video-container-${popup.camera.english}`" class="video-js-container"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from "vue";
import * as echarts from "echarts";
import handanMapJson from "../assets/yn_and_feixiang.json";
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import '@videojs/http-streaming';

// --- ECharts & DOM ---
const chartRef = ref<HTMLDivElement>();
let myChart: echarts.ECharts;
let resizeObserver: ResizeObserver;
const popupRefs = ref<HTMLDivElement[]>([]); // 用于获取弹窗的 DOM 引用

// --- 弹窗和视频播放器状态 ---
// 使用一个数组来管理所有弹窗
const activePopups = ref<any[]>([]);
// 使用一个 Map 来管理多个播放器实例
const players = new Map<string, videojs.Player>();
const lines = ref<any[]>([]); // 存储连接线的坐标

// --- API & 数据 ---
const appKey = 'd4baaab8baf24baa9541f1bbe64b2200';
const appSecret = 'f42fb82edaed28c57b2045d882f0208e';

const cameraData = ref([
    { id: 1, name: '永年', english: 'yn', deviceSerial: '33011063992677425735:33010516991327760034', view: 'view1', value: [114.5569, 36.7897] },
    { id: 2, name: '肥乡北', english: 'fx_n', deviceSerial: '33011063992677425735:33010084991327588111', view: 'view1', value: [114.7002, 36.5716] },
    { id: 3, name: '肥乡南', english: 'fx_s', deviceSerial: '33011063992677425735:33011012991327147072', view: 'view1', value: [114.7002, 36.5716] },
    { id: 4, name: '肥乡梁厂', english: 'fx_lc', deviceSerial: '33011063992677425735:33011033991327056374', view: 'view1', value: [114.7002, 36.5716] }
]);

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
    center: [114.70, 36.72],
    roam: true,
    itemStyle: { // 地图区域的默认样式
      areaColor: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: '#073684' }, { offset: 1, color: '#061E3D' }]
      },
      borderColor: '#2B91B7',
      borderWidth: 1,
    },
    // 新增 label 配置，用于显示区域名称
    label: {
      show: true,       // 显示标签
      color: '#ffffff', // 标签文字颜色
      fontSize: 14,     // 字体大小
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
      label: { show: false, position: 'bottom', formatter: '{b}', color: '#fff', fontSize: 12 },
      emphasis: { scale: 1.5 },
      rippleEffect: { brushType: 'stroke', scale: 3 }
    },
  ],
};

// --- 核心功能函数 ---

/**
 * 根据摄像头名称计算弹窗的智能定位样式
 */
const getPopupPositionStyle = (cameraName: string, point: number[]) => {
  if (!point || typeof point[0] !== 'number' || typeof point[1] !== 'number') {
    console.error(`Invalid point for camera ${cameraName}`, point);
    return { display: 'none' }; // 如果坐标无效则隐藏弹窗
  }
  
  const baseStyle = { left: `${point[0]}px`, top: `${point[1]}px` };
  
  // **FIX**: 返回一个包含多个 CSS 变量的对象，而不是一个拼接的字符串
  // 这样更清晰，且避免了 Vue 的警告
  let popupTransform = 'translate(-50%, -50%)'; // 弹窗主体的位置
  let afterStyles: any = { // 伪元素 (小三角) 的样式
    '--after-border-color': 'transparent transparent #4db6e5 transparent',
    '--after-bottom': '-10px',
    '--after-left': '50%',
    '--after-transform': 'translateX(-50%)',
  };

  switch (cameraName) {
    case '永年': // 右上侧
      popupTransform = 'translate(20%, -110%)';
      afterStyles = {
        '--after-border-color': 'transparent transparent transparent #4db6e5',
        '--after-top': '95%',
        '--after-left': '-10px',
        '--after-transform': 'translateY(-50%)',
      };
      break;
    case '肥乡北': // 左上侧
      popupTransform = 'translate(70%, -163%)';
       afterStyles = {
        '--after-border-color': 'transparent #4db6e5 transparent transparent',
        '--after-top': '95%',
        '--after-right': '-10px',
        '--after-transform': 'translateY(-50%)',
      };
      break;
    case '肥乡梁厂': // 上侧
      popupTransform = 'translate(70%, -26%)';
      afterStyles = { // 默认就是朝上，这里可以不改，但为了清晰还是写出来
        '--after-border-color': '#4db6e5 transparent transparent transparent',
        '--after-top': '-10px',
        '--after-left': '50%',
        '--after-transform': 'translateX(-50%)',
      };
      break;
    case '肥乡南': // 左侧
      popupTransform = 'translate(-136%, -70%)';
      afterStyles = {
        '--after-border-color': 'transparent transparent transparent #4db6e5',
        '--after-top': '50%',
        '--after-left': '-10px',
        '--after-transform': 'translateY(-50%)',
      };
      break;
  }
  
  return { ...baseStyle, transform: popupTransform, ...afterStyles };
  // let transform = 'translate(-50%, -50%)'; // 默认居中
  // let afterBorder = 'border-bottom: 10px solid #4db6e5;'; // 默认尖角朝上

  // switch (cameraName) {
  //   case '永年': // 右上侧
  //     transform = 'translate(10%, -110%)';
  //     afterBorder = 'border-left: 10px solid #4db6e5; left: -10px; top: 95%; transform: translateY(-50%) rotate(45deg);';
  //     break;
  //   case '肥乡北': // 左上侧
  //     transform = 'translate(-110%, -110%)';
  //     afterBorder = 'border-right: 10px solid #4db6e5; right: -10px; top: 95%; transform: translateY(-50%) rotate(-45deg);';
  //     break;
  //   case '肥乡梁厂': // 上侧
  //     transform = 'translate(-50%, -120%)'; // 向上多偏移一点
  //     afterBorder = 'border-top: 10px solid #4db6e5; bottom: -10px; left: 50%; transform: translateX(-50%);';
  //     break;
  //   case '肥乡南': // 左侧
  //     transform = 'translate(-115%, -50%)';
  //     afterBorder = 'border-left: 10px solid #4db6e5; right: -10px; top: 50%; transform: translateY(-50%);';
  //     break;
  // }
  
  // return { ...baseStyle, transform, '--after-border': afterBorder };
};

/**
 * **修改**: 初始化图表，但不绑定点击事件
 */
const initChart = () => {
  if (!chartRef.value) return;
  myChart = echarts.init(chartRef.value);
  echarts.registerMap("handan", handanMapJson as any);
  myChart.setOption(option);
};

/**
 * **新增**: 页面加载时自动打开所有弹窗并播放视频
 */
const openAllPopups = async () => {
  if (!myChart) return;
  
  try {
    const token = await getValidAccessToken();
    
    // **修改点 2**: 使用 for...of 循环代替 map，更好地控制异步流程
    for (const camera of cameraData.value) {
      const pointInPixel = myChart.convertToPixel('geo', camera.value);
      const style = getPopupPositionStyle(camera.name, pointInPixel);
      // 创建 popup 对象并立即推入数组，触发 UI 渲染
      const popup = { camera, style, loading: true };
      activePopups.value.push(popup);

      // 异步获取视频流，不阻塞下一个摄像头的处理
      (async () => {
        try {
          const videoUrl = await fetchCameraUrl(token, camera);
          
          // 找到刚刚添加的 popup 对象并更新它的 loading 状态
          const targetPopup = activePopups.value.find(p => p.camera.deviceSerial === camera.deviceSerial);
          if (targetPopup) {
            targetPopup.loading = false;
            
            // **修改点 3**: 将播放器初始化放在 nextTick 回调中
            // 确保 DOM 更新（v-if 切换）完成后再执行
            nextTick(() => {
              initVideoPlayer(camera, videoUrl);
            });
          }
        } catch (e) {
          console.error(`无法加载 ${camera.name} 的视频:`, e);
          const targetPopup = activePopups.value.find(p => p.camera.deviceSerial === camera.deviceSerial);
          if (targetPopup) {
            targetPopup.loading = false; // 即使失败也要停止加载状态
          }
        }
      })();
    }

  } catch (error) {
    alert("初始化摄像头失败，请检查网络或API配置。");
    console.error(error);
  }
};

/**
 * **新增**: 处理弹窗点击事件，跳转到标注页面
 */
const handlePopupClick = (camera: any) => {
  const tokenInfo = JSON.parse(localStorage.getItem('ys7TokenInfo') || 'null');
  if (!tokenInfo || !tokenInfo.accessToken) {
    alert("无法获取有效的 Access Token，请刷新页面后重试。");
    return;
  }
  
  // 从 DataScreen.vue 借鉴的逻辑
  const url = `/annotation?accessToken=${tokenInfo.accessToken}&cameraName=${encodeURIComponent(camera.english)}&view=${camera.view}`;
  window.open(url, '_blank');
};


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
 * **修改**: 初始化播放器，并将其存入 Map
 */
const initVideoPlayer = (camera: any, url: string) => {
  const playerId = camera.english;
  // 先销毁已存在的同名播放器
  if (players.has(playerId)) {
    players.get(playerId)?.dispose();
  }
  
  const videoOptions: videojs.PlayerOptions = {
    autoplay: true,
    muted: true,
    controls: false, // 隐藏默认控件，因为窗口很小
    preload: 'auto',
    fluid: true,
    sources: [{ src: url, type: 'application/x-mpegURL' }]
  };

  const videoContainer = document.getElementById(`video-container-${playerId}`);
  if (videoContainer) {
    videoContainer.innerHTML = `<video class="video-js vjs-default-skin"></video>`;
    const videoElement = videoContainer.querySelector('video');
    
    if (videoElement) {
        const player = videojs(videoElement, videoOptions, () => {
          player.play().catch(e => console.error(`自动播放 ${camera.name} 失败:`, e));
        });
        players.set(playerId, player); // 存入Map
    }
  }
};

// --- Vue 生命周期钩子 ---
onMounted(() => {
  nextTick(() => {
    initChart();
    
    // **修改**: 在图表初始化后，自动打开所有弹窗
    openAllPopups();

    if (chartRef.value) {
      resizeObserver = new ResizeObserver(() => {
        myChart?.resize();
        // **新增**: 窗口大小变化时，重新计算弹窗位置
        activePopups.value.forEach(popup => {
          const point = myChart.convertToPixel('geo', popup.camera.value);
          popup.style = getPopupPositionStyle(popup.camera.name, point);
        });
      });
      resizeObserver.observe(chartRef.value);
    }
  });
});

onBeforeUnmount(() => {
  // 销毁所有播放器实例
  players.forEach(player => player.dispose());
  players.clear();

  if (myChart) {
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
}

.echarts-map {
  width: 100%;
  height: 100%;
}

.video-popup {
  position: absolute;
  /* **修改**: 尺寸变小 */
  width: 270px; 
  height: 183px;
  background-color: #0c2049;
  border: 1px solid #4db6e5;
  border-radius: 8px;
  box-shadow: 0 0 20px rgba(0, 208, 255, 0.5);
  z-index: 100;
  display: flex;
  flex-direction: column;
  cursor: pointer; /* 提示用户可以点击 */
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.video-popup:hover {
  transform: scale(1.05); /* 鼠标悬浮时放大，提供交互感 */
  box-shadow: 0 0 30px rgba(0, 208, 255, 0.8);
  z-index: 101; /* 确保悬浮的在最上层 */
}

/* **FIX**: 修改伪元素样式，使用多个 CSS 变量来控制小三角 */
.video-popup::after {
  content: '';
  position: absolute;
  width: 0;
  height: 0;
  border-width: 10px;
  border-style: solid;
  /* 通过变量应用样式 */
  border-color: var(--after-border-color);
  top: var(--after-top, auto);
  bottom: var(--after-bottom, auto);
  left: var(--after-left, auto);
  right: var(--after-right, auto);
  transform: var(--after-transform, none);
}
/* **新增**: 使用 CSS 变量来动态设置尖角样式 */
/* .video-popup::after {
  content: '';
  position: absolute;
  width: 0;
  height: 0;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent; */
  /* 通过变量应用样式 */
  /* border-image: var(--after-border); 
} */

.popup-header {
  display: flex;
  justify-content: center; /* 居中标题 */
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
  position: relative; /* 添加相对定位，确保子元素可以相对于它定位 */
}

/* **修改**: 让加载提示和视频容器可以重叠 */
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
  height: 100%;
  font-size: 14px;
  z-index: 2; /* 确保加载提示在上方 */
  background-color: #000; /* 加上背景色以覆盖下方内容 */
}

.video-js-container {
  width: 100%;
  height: 100%;
  z-index: 1;
}
</style>