<template>
  <div class="annotator-container">
    <div class="video-container">
      <video ref="videoPlayer" class="video-js vjs-default-skin"></video>
    </div>
    
    <canvas
      ref="annotationCanvas"
      class="annotation-canvas-layer"
      @mousemove="handleCanvasMouseMove"
      :style="{ cursor: canvasCursor }"
    ></canvas>

    <div class="ui-overlay">
      <header class="app-header">
        <h1>智慧监管平台</h1>
        <div class="connection-status">
            <div class="status-indicator" :class="{ connected: isVideoPlaying }"></div>
            <span>{{ videoStatus }}</span>
        </div>
      </header>

      <div 
        class="drawer-container"
        @mouseenter="isCameraDrawerOpen = true"
        @mouseleave="isCameraDrawerOpen = false"
      >
        <div class="drawer-panel" :class="{ 'is-open': isCameraDrawerOpen }">
          <div class="controls-group camera-controls">
            <!-- 动态生成摄像头按钮 -->
            <button 
              v-for="camera in cameras" 
              :key="camera.id"
              @click="switchCamera(camera.id)" 
              class="control-btn" 
              :class="{ selected: currentCameraId === camera.id }"
            >
              {{ camera.name }}
            </button>
          </div>
          <div class="drawer-handle">
            <span>摄<br>像<br>头</span>
          </div>
        </div>
      </div>

      <div class="top-controls-container">
        <div class="controls-group view-controls">
          <!-- 动态生成视图按钮 -->
          <button 
            v-for="view in views" 
            :key="view.id"
            @click="switchView(view.id)" 
            class="control-btn" 
            :class="{ selected: currentViewId === view.id }"
            :disabled="!view.enabled"
          >
            {{ view.name }}
          </button>
        </div>
      </div>

      <main class="main-content">
        <div v-if="hoveredAnnotation" class="details-popup" :style="{ top: popupPosition.y + 'px', left: popupPosition.x + 'px' }">
          <h4>{{ hoveredAnnotation.title }}</h4>
          <p>{{ hoveredAnnotation.details }}</p>
        </div>
      </main>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue';

// --- 导入 Video.js 及其 HLS 插件 ---
import videojs from 'video.js';
import 'video.js/dist/video-js.css'; // 导入 Video.js 的 CSS

// --- 配置Configuration ---
const cameras = ref({
  yn: { 
    id: 'yn', 
    name: '永年', 
    url: 'https://open.ys7.com/v3/openlive/33011063992677425735:33010516991327760034_1_1.m3u8?expire=1783839126&id=865969116245139456&t=041a0c22eee09600f9928249aec5625ec46b6bbfc78e805813fff17561347d91&ev=100&devProto=gb28181', 
    viewCount: 3, 
    deviceSerial: '33011063992677425735:33010516991327760034' 
  },
  fx_n: { 
    id: 'fx_n', 
    name: '肥乡北', 
    url: 'https://open.ys7.com/v3/openlive/33011063992677425735:33010084991327588111_1_1.m3u8?expire=1783839201&id=865969431971373056&t=7cc28dde7d721171e7d1d482f643c2438c5bb4b1c39f23b2a68e1bac9363758d&ev=100&devProto=gb28181', 
    viewCount: 3, 
    deviceSerial: '33011063992677425735:33010084991327588111' 
  },
  fx_s: { 
    id: 'fx_s', 
    name: '肥乡南', 
    url: 'https://open.ys7.com/v3/openlive/33011063992677425735:33011012991327147072_1_1.m3u8?expire=1783839181&id=865969347674099712&t=402c3fd77bd2c00d25295f63150285f372139bfb4581931825b46ca393bffcdd&ev=100&devProto=gb28181', 
    viewCount: 3, 
    deviceSerial: '33011063992677425735:33011012991327147072' 
  },
  fx_lc: { 
    id: 'fx_lc', 
    name: '肥乡梁厂', 
    url: 'https://open.ys7.com/v3/openlive/33011063992677425735:33011033991327056374_1_1.m3u8?expire=1783839161&id=865969264091918336&t=a65166c636992ea20b0f7fc48a6803036e40b0187379097b10650231ec5461fc&ev=100&devProto=gb28181', 
    viewCount: 1, 
    deviceSerial: '33011063992677425735:33011033991327056374' 
  }
});

// 不同标注类型的颜色映射
const typeColors = {
  '盖梁': '#FFA500', // 橙色
  '桥墩': '#FFD700', // 黄色
  '通道': '#32CD32', // 绿色
  '匝道': '#1E90FF', // 蓝色
  '方向': '#FF4500',  // 红色
  '桥台': '#00FFFF',  // 青色 (Cyan)
  '涵洞': '#8A2BE2'   // 紫色 (BlueViolet)
};

// --- 状态管理 ---
// --- Canvas 和状态管理 ---
const annotationCanvas = ref(null);
let annotationCtx = null;

const annotations = ref([]); // 保存来自后端的标注数据
const hoveredAnnotation = ref(null); // 保存当前鼠标悬停的标注
const popupPosition = ref({ x: 0, y: 0 }); // 详情弹出框的位置
const canvasCursor = ref('default'); // 用于在悬停时将光标变为'pointer'

// --- 摄像头和视角状态 ---
const currentCameraId = ref('yn'); // 默认选中'永年'摄像头
const currentViewId = ref('view1'); // 默认选中视角1
const isCameraDrawerOpen = ref(false); // 控制抽屉状态

// --- Video.js 播放器状态 ---
const videoPlayer = ref(null); // 用于 <video> 元素的模板引用
const player = ref(null);      // 用于持有 Video.js 播放器实例
const isVideoPlaying = ref(false);
const videoStatus = ref("播放器准备就绪");

// --- Computed Properties ---
const currentCamera = computed(() => cameras.value[currentCameraId.value]);

const views = computed(() => {
  const viewCount = currentCamera.value.viewCount;
  return Array.from({ length: 6 }, (_, i) => {
    const viewNum = i + 1;
    return {
      id: `view${viewNum}`,
      name: `视角${viewNum}`,
      enabled: viewNum <= viewCount
    };
  });
});

// --- 组件生命周期钩子 ---
onMounted(() => {
  // 确保 DOM 已经渲染
  nextTick(() => {
    initPlayer(currentCamera.value.url); // 初始化 Video.js
    initCanvas();
    // fetchAnnotations(); // 组件加载时获取标注
    window.addEventListener('resize', handleResize);
    // 初始加载：切换到默认摄像头和视角
    switchCamera(currentCameraId.value, true);
  });
  
});

onUnmounted(() => {
  // 销毁播放器以释放资源
  if (player.value) {
    player.value.dispose();
  }
  window.removeEventListener('resize', handleResize);
});

// --- Video.js 播放器初始化 ---
/**
 * 初始化 Video.js 播放器。
 * 关键：在 options 中直接提供初始的 HLS 源。
 * @param {string} initialUrl - 第一个要播放的视频流地址
 */
const initPlayer = (initialUrl) => {
  if (!videoPlayer.value) return;

  const options = {
    autoplay: true,    // 自动播放
    muted: true,       // 静音以允许在大多数浏览器中自动播放
    controls: true,    // 显示默认播放器控件
    preload: 'auto',
    fluid: false,       // 播放器将占满容器宽度，并保持宽高比
    responsive: true,
    sources: [{
      src: initialUrl,
      type: 'application/x-mpegURL' // HLS 视频流类型
    }]
  };

  player.value = videojs(videoPlayer.value, options, () => {
    if (!player.value) {
      console.error("播放器尚未初始化！");
      return;
    }
    console.log('Video.js播放器准备就绪');
    player.value.play().catch(error => {
      console.error("自动播放被浏览器阻止:", error);
      videoStatus.value = "点击播放以开始";
    });
  });

  // 播放器事件监听
  player.value.on('playing', () => {
    isVideoPlaying.value = true;
    videoStatus.value = "视频流播放中";
    console.log('Video stream is playing.');
  });

  player.value.on('error', function() {
    const error = player.value.error();
    isVideoPlaying.value = false;
    videoStatus.value = `播放错误: ${error?.message || '未知错误'}`;
    console.error('Video.js Error:', error);
  });
  
  player.value.on('ended', () => {
    isVideoPlaying.value = false;
    videoStatus.value = '播放结束';
  });
  
  player.value.on('pause', () => {
    isVideoPlaying.value = false;
    videoStatus.value = '已暂停';
  });
};

/**
 * 灵活更换视频流的函数。
 * 这个函数现在可以安全地被随时调用。
 * @param {string} url - 新的 HLS 视频流地址
 */
const setVideoStream = (url) => {
  if (!player.value) {
    console.error("播放器尚未初始化！");
    return;
  }
  console.log(`正在更换视频源为: ${url}`);
  player.value.src({
    src: url,
    type: 'application/x-mpegURL' // HLS 流类型
  });
  player.value.play().catch(error => {
      console.error("播放新视频源失败:", error);
      videoStatus.value = "无法播放新的视频源";
  });
};

// --- Canvas 和绘制 ---
const initCanvas = () => {
    // 变更：标注画布现在需要匹配视频容器的尺寸
    const container = document.querySelector('.video-container');
    if (!container || !annotationCanvas.value) return;

    // Canvas 尺寸直接匹配容器尺寸
    const { clientWidth: width, clientHeight: height } = container;

    annotationCanvas.value.width = width;
    annotationCanvas.value.height = height;
    
    annotationCtx = annotationCanvas.value.getContext('2d');
    
    drawAnnotations(); // 窗口大小调整时重绘标注
};

// 优化了handleResize，现在只进行重绘，不再重新获取数据
// 窗口大小调整时，重新初始化 Canvas 即可
const handleResize = () => {
    initCanvas(); // initCanvas 会重设画布大小并调用 drawAnnotations
};

// 将 `annotations` ref 中存储的所有标注绘制到画布上。
const drawAnnotations = () => {
  if (!annotationCtx) return;
  // 获取当前画布的实时尺寸
  const currentCanvasWidth = annotationCtx.canvas.width;
  const currentCanvasHeight = annotationCtx.canvas.height;
  
  annotationCtx.clearRect(0, 0, currentCanvasWidth, currentCanvasHeight);

  annotations.value.forEach(anno => {
    const color = typeColors[anno.type] || '#FFFFFF'; 
    const coordinates = anno.coordinates;

    // 检查是否存在必要的尺寸信息
    if (!coordinates || coordinates.length < 2 || !anno.imageWidth || !anno.imageHeight) return;

    // 缩放比例基于 Canvas 尺寸，而 Canvas 尺寸等于容器尺寸
    const scaleX = currentCanvasWidth / anno.imageWidth;
    const scaleY = currentCanvasHeight / anno.imageHeight;

    annotationCtx.lineWidth = 3;
    annotationCtx.strokeStyle = color;
    annotationCtx.fillStyle = `${color}4D`; // 30% 透明度填充

    annotationCtx.beginPath();
    // 对每个坐标点应用缩放比例
    const startX = coordinates[0].x * scaleX;
    const startY = coordinates[0].y * scaleY;
    annotationCtx.moveTo(startX, startY);

    for (let i = 1; i < coordinates.length; i++) {
      const nextX = coordinates[i].x * scaleX;
      const nextY = coordinates[i].y * scaleY;
      annotationCtx.lineTo(nextX, nextY);
    }

    annotationCtx.closePath();
    annotationCtx.stroke();
    annotationCtx.fill();

    // 对文本位置同样应用缩放
    annotationCtx.fillStyle = '#FFFFFF';
    annotationCtx.font = 'bold 16px Arial';
    annotationCtx.textBaseline = 'top';
    const textX = startX + 10; // 在缩放后的坐标基础上偏移
    const textY = startY + 10;
    annotationCtx.fillText(anno.title, textX, textY);
  });
};


// --- 后端数据与交互 ---
const fetchAnnotations = async (location, view) => {
  console.log(`正在从后台获取标注数据: ${location}, view: ${view}`);
  annotations.value = []; // 清空之前的标注
  const url = `http://59.110.65.210:8081/label?location=${location}&view=${view}`;
  try {
    const response = await fetch(url, { method: 'GET' });
    if (!response.ok) throw new Error(`Network response was not ok (${response.status})`);
    
    const data = await response.json();
    annotations.value = data;
    console.log("标注数据加载成功:", annotations.value);
    drawAnnotations();
  } catch (error) {
    console.error("获取标注数据失败:", error);
    alert(`无法加载标注数据: ${error.message}`);
  }
};

/**
 * 切换摄像头的预留函数
 * @param {string} cameraId - 要切换到的摄像头ID
 */
const switchCamera = async (cameraId, isInitialLoad = false) => {
  console.log(`切换到摄像头: ${cameraId}`);
  currentCameraId.value = cameraId;

  // 切换摄像头时，总是重置为 view1
  const defaultView = 'view1';
  currentViewId.value = defaultView;

  // 更新视频流
  const newUrl = currentCamera.value.url;
  setVideoStream(newUrl);

  // 切换到新摄像头的默认视图
  await switchView(defaultView, true);
};

/**
 * 通过向后端发送命令来切换视图。
 * 这通常会触发视频流的更改和一套新的标注。
 * CHANGE: 通过向萤石云API发送命令来切换设备预设点（视角）。
 * @param {string} viewId - 要切换到的视图ID (例如 'view1')。
 */
// 此函数现在也会更新视频播放器的源
const switchView = async (viewId, isCameraSwitch = false) => {
  console.log(`准备切换到视角: ${viewId}`);
  currentViewId.value = viewId; // 更新当前视角状态

  // 预设切换逻辑 (API 调用)
  const indexMatch = viewId.match(/(\d+)$/);
  if (!indexMatch) {
    console.error(`无效的视角ID格式: ${viewId}`);
    // alert(`视角ID "${viewId}" 格式不正确。`);
    return;
  }
  const index = parseInt(indexMatch[1], 10);
  
  // 注意：这将调用萤石云API来移动摄像头。
  // 警告: accessToken 通常具有时效性，不应硬编码在前端。
  // 在生产环境中，应由后端服务器管理和提供。
  // 我们将假设流URL保持不变，因为是流内容本身发生了变化。
  // 如果每个预设点都有一个*不同*的M3U8 URL，您需要在此处更新它。
  const accessToken = "at.4zp9f112a1yqew826m38jxep7pzs23hh-8dx62y4kqh-0gfatka-mtf9dfjlw";
  const deviceSerial = currentCamera.value.deviceSerial;
  const channelNo = 1;
  const apiUrl = `https://open.ys7.com/api/lapp/device/preset/move?accessToken=${accessToken}&deviceSerial=${deviceSerial}&index=${index}&channelNo=${channelNo}`;

  try {
    const response = await fetch(apiUrl, { method: 'POST' });
    const result = await response.json();
    const timestamp = new Date().toLocaleTimeString();

    // 萤石云API成功响应码为'200'
    if (response.ok && result.code === '200') {
      console.log(`[${timestamp}] 视角${viewId}切换成功 (${response.status}):`, result);
      // 成功切换视角后，可以获取新视角的标注
      await fetchAnnotations(currentCameraId.value, viewId);
    } else {
      // 处理API返回的业务错误
      console.error(`[${timestamp}] 视角切换API错误 (${response.status}):`, result);
      throw new Error(`API 错误: ${result.msg || '未知错误'}`);
    }
  } catch (error) {
    const timestamp = new Date().toLocaleTimeString();
    console.error(`[${timestamp}] 切换到 ${viewId} 的网络请求失败:`, error);
    alert(`指令 "${viewId}" 发送失败: ${error.message}`);
  }
};

// --- 用于详情弹出框的鼠标交互 ---
/**
 * 使用射线投射算法检查一个点是否在多边形内部。
 * @param {{x: number, y: number}} point 鼠标位置。
 * @param {Array<{x: number, y: number}>} polygon 标注图形的顶点数组。
 * @returns {boolean} 如果点在多边形内，则返回true。
 */
function isPointInPolygon(point, polygon) {
    let isInside = false;
    const x = point.x, y = point.y;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
        const xi = polygon[i].x, yi = polygon[i].y;
        const xj = polygon[j].x, yj = polygon[j].y;
        const intersect = ((yi > y) !== (yj > y))
            && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
        if (intersect) isInside = !isInside;
    }
    return isInside;
}

const handleCanvasMouseMove = (e) => {
  if (!annotationCanvas.value) return;
  const rect = annotationCanvas.value.getBoundingClientRect();
  const mousePos = { x: e.clientX - rect.left, y: e.clientY - rect.top };

  // --- 悬停检测也需要使用缩放后的坐标 ---
  const currentCanvasWidth = annotationCanvas.value.width;
  const currentCanvasHeight = annotationCanvas.value.height;

  const currentHover = annotations.value.slice().reverse().find(anno => {
      if (!anno.imageWidth || !anno.imageHeight) return false;
      const scaleX = currentCanvasWidth / anno.imageWidth;
      const scaleY = currentCanvasHeight / anno.imageHeight;

      // 将原始坐标转换为当前画布坐标以进行比较
      const scaledPolygon = anno.coordinates.map(p => ({ x: p.x * scaleX, y: p.y * scaleY }));
      return isPointInPolygon(mousePos, scaledPolygon);
  });

  if (currentHover) {
    hoveredAnnotation.value = currentHover;
    popupPosition.value.x = Math.min(mousePos.x + 15, rect.width - 260); 
    popupPosition.value.y = Math.min(mousePos.y + 15, rect.height - 110); 
    canvasCursor.value = 'pointer';
  } else {
    hoveredAnnotation.value = null;
    canvasCursor.value = 'default';
  }
};
</script>

<style scoped>
.annotator-container {
  position: relative; width: 100vw; height: 100vh;
  background-color: #000; overflow: hidden;
  font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* --- 用于容纳播放器的视频容器 --- */
.video-container {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
}

/* video.js 内部的 video 元素拉伸填充 */
.video-container :deep(.video-js .vjs-tech) {
  object-fit: fill;
}

/* --- 让 Video.js 自己处理尺寸 --- */
.video-js {
    width: 100%;
    height: 100%;
}

.video-container :deep(.video-js .vjs-control-bar) {
  display: none; /* 隐藏 Video.js 的控制栏 */
}

.annotation-canvas-layer {
  position: absolute; 
  top: 0; 
  left: 0;
  /* 变更：尺寸现在由 initCanvas 处理，但要确保它在视频之上 */
  width: 100%; 
  height: 100%;
  z-index: 3;
}

.ui-overlay {
  position: absolute; 
  top: 0; 
  left: 0; 
  width: 100%; 
  height: 100%;
  z-index: 4; 
  pointer-events: none; 
  display: flex; 
  flex-direction: column;
}

.main-content { 
  flex-grow: 1; 
  position: relative; 
}

/* --- 头部 --- */
.app-header {
  position: relative; height: 50px; width: 100%; color: #fff;
  background: linear-gradient( to right, 
    rgba(0, 191, 255, 0) 0%, 
    rgba(0, 191, 255, 0.8) 30%, 
    rgba(0, 191, 255, 1) 50%, 
    rgba(0, 191, 255, 0.8) 70%, 
    rgba(0, 191, 255, 0) 100% 
  );
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8), 0 0 10px rgba(0, 191, 255, 0.5);
  flex-shrink: 0;
}
.app-header h1 {
  position: absolute; 
  left: 50%; 
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 2.5rem;
  font-weight: 600;
}
.connection-status {
  position: absolute; 
  right: 20px; 
  top: 50%;
  transform: translateY(-50%);
  display: flex; 
  align-items: center; 
  gap: 8px; 
  font-size: 0.9rem;
}
.status-indicator {
  width: 12px; 
  height: 12px; 
  border-radius: 50%; 
  background-color: #ff5722;
  box-shadow: 0 0 8px #ff5722; 
  transition: all 0.3s ease;
}
.status-indicator.connected {
  background-color: #00ff7f; 
  box-shadow: 0 0 10px #00ff7f;
}

/* --- 抽屉式面板 --- */
.drawer-container {
  position: absolute;
  top: 65px;
  left: 0;
  z-index: 50;
  pointer-events: auto;
  height: 200px; /* 定义一个悬停区域高度 */
}
.drawer-panel {
  position: absolute;
  top: 0;
  left: 0;
  padding: 20px;
  background-color: rgba(10, 40, 90, 0.9);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 191, 255, 0.6);
  border-left: none;
  border-radius: 0 12px 12px 0;
  transform: translateX(-100%);
  transition: transform 0.4s ease-in-out;
  overflow: visible; /* 关键：允许子元素(手柄)在外部显示 */
}
.drawer-panel.is-open {
  transform: translateX(0);
  box-shadow: 10px 0 25px rgba(0, 0, 0, 0.3);
}
.drawer-handle {
  position: absolute;
  top: 0;
  left: 100%; /* 关键：定位在父元素(面板)的右侧 */
  width: 35px;
  height: 100%; 
  background-color: rgba(0, 191, 255, 0.8);
  border-radius: 0 10px 10px 0;
  box-shadow: 0 0 12px rgba(0, 191, 255, 0.7);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 1rem;
  line-height: 1.5;
  text-orientation: mixed;
  white-space: nowrap; /* 防止文字换行 */
  transition: background-color 0.3s;
}
.drawer-container:hover .drawer-handle {
  background-color: rgba(0, 191, 255, 1);
}

/* --- 顶部右侧控件 --- */
.top-controls-container {
  position: absolute; 
  top: 65px; 
  right: 20px; 
  pointer-events: none;
}
.controls-group {
  pointer-events: auto; 
  display: grid; 
  gap: 8px;
}
.camera-controls {
  grid-template-columns: 1fr 1fr; 
  width: 280px;
}
.view-controls {
  grid-template-columns: 1fr 1fr 1fr; 
  width: 240px;
}
.control-btn {
  padding: 12px 10px; 
  font-size: 1rem; 
  font-weight: 600;
  color: #fff; 
  background-color: rgba(20, 40, 80, 0.7);
  border: 1px solid rgba(0, 191, 255, 0.6); 
  border-radius: 8px;
  cursor: pointer; 
  transition: all 0.2s ease; 
  backdrop-filter: blur(5px);
  text-align: center;
}
.control-btn:hover {
  background-color: rgba(0, 191, 255, 0.7); 
  border-color: #fff; 
  transform: scale(1.05);
}
.control-btn:active { transform: scale(0.98); }
.control-btn.selected {
  background-color: #00BFFF; 
  border-color: #fff;
  box-shadow: 0 0 12px rgba(0, 191, 255, 0.8); 
  color: #0d203e; 
  transform: scale(1.05);
}

/* 用于禁用状态的按钮样式 */
.control-btn:disabled {
  background-color: rgba(50, 60, 80, 0.5);
  border-color: rgba(100, 110, 130, 0.5);
  color: rgba(255, 255, 255, 0.4);
  cursor: not-allowed;
  transform: none;
}
.control-btn:disabled:hover {
  background-color: rgba(50, 60, 80, 0.5);
  transform: none;
}

/* --- 详情弹出框 --- */
.details-popup {
  position: absolute; 
  width: 250px; 
  padding: 15px;
  background-color: rgba(10, 40, 90, 0.85); 
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 191, 255, 0.6); 
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  color: #fff; 
  font-size: 0.9rem; 
  pointer-events: none;
  transition: opacity 0.2s ease; 
  z-index: 100;
}
.details-popup h4 {
  margin: 0 0 10px 0; 
  color: #00BFFF; 
  font-size: 1rem;
  border-bottom: 1px solid rgba(0, 191, 255, 0.3); 
  padding-bottom: 5px;
}
.details-popup p { 
  margin: 0; 
  line-height: 1.5; 
}
</style>