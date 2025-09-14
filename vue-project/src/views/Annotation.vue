<template>
  <div class="annotator-container" @click="handleGlobalClick">
    <div ref="videoContainer" class="video-container">
    </div>
    
    <canvas
      ref="annotationCanvas"
      class="annotation-canvas-layer"
      @mousemove="handleCanvasMouseMove"
      :style="{ cursor: canvasCursor }"
    ></canvas>

    <div class="ui-overlay">
      <header class="app-header">
        <h1>互通施工关键流程的智慧管理平台</h1>
        <div class="connection-status">
            <div class="status-indicator" :class="{ connected: isVideoPlaying }"></div>
            <span>{{ videoStatus }}</span>
        </div>
      </header>

      <div class="drawer-container">
        <div class="drawer-panel" :class="{ 'is-open': isCameraDrawerOpen }">
          <div class="controls-group camera-controls">
            <button 
              v-for="camera in cameras" 
              :key="camera.id"
              @click="switchCamera(camera.id)" 
              class="control-btn" 
              :class="{ selected: currentCameraId === camera.id }"
              :disabled="isLoading"
            >
              {{ camera.name }}
            </button>
          </div>
          <div class="drawer-handle" @click.stop="toggleCameraDrawer">
            <span>摄<br>像<br>头</span>
          </div>
        </div>
      </div>

      <div class="top-controls-container">
        <div class="controls-group view-controls">
          <button 
            v-for="view in views" 
            :key="view.id"
            @click="switchView(view.id)" 
            class="control-btn" 
            :class="{ selected: currentViewId === view.id }"
            :disabled="!view.enabled || isLoading"
          >
            {{ view.name }}
          </button>
        </div>
      </div>

      <main class="main-content">
        <div v-if="hoveredAnnotation" class="details-popup" :style="{ top: popupPosition.y + 'px', left: popupPosition.x + 'px' }">
          <h4>{{ hoveredAnnotation.title }}</h4>
          <p v-html="formattedPopupDetails"></p>
        </div>
      </main>
    </div>

    <div class="loading-overlay" v-show="isViewSwitching">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <div class="loading-text">加载视频中，请稍候...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue';
import { useRoute } from 'vue-router';

import EZUIKit from 'ezuikit-js';

const cameras = ref({
   yn: { id: 'yn', name: '永年', viewCount: 3, deviceSerial: '33011063992677425735:33010516991327760034' },
   fx_n: { id: 'fx_n', name: '肥乡北', viewCount: 3, deviceSerial: '33011063992677425735:33010084991327588111' },
   fx_s: { id: 'fx_s', name: '肥乡南', viewCount: 3, deviceSerial: '33011063992677425735:33011012991327147072' },
   fx_lc: { id: 'fx_lc', name: '肥乡梁场', viewCount: 1, deviceSerial: '33011063992677425735:33011033991327056374' }
});

// label.json数据缓存
let labelData = null;

// --- 为播放器添加重试逻辑 ---
const playerMaxRetries = 5; // 最大重试次数
const playerRetryCounter = ref(0);
const playerRetryDelay = 5000; // 重试间隔 (5秒)

const typeColors = {
  '盖梁': '#FF8C00',
  '箱梁': '#FFA500',
  '桥墩': '#FFD700',
  '桥台': '#F0E68C',
  '预制梁': '#FF6347',
  '跨': '#CD853F',

  '方向': '#FF4500',
  '匝道': '#1E90FF',
  '通道': '#32CD32',
  '收费站': '#9370DB',

  '支座': '#00FFFF',
  '挡块': '#B0C4DE',
  '涵洞': '#9932CC',
  '台座': '#FF0000',
  '路肩墙': '#708090',

  '其他': '#FFFFFF'
};

const annotationCanvas = ref(null);
let annotationCtx = null;

const annotations = ref([]);
const hoveredAnnotation = ref(null);
const popupPosition = ref({ x: 0, y: 0 });
const canvasCursor = ref('default');

const route = useRoute();
const accessToken = ref('');

const currentCameraId = ref('');
const currentViewId = ref('view1');
const isCameraDrawerOpen = ref(false);
const isLoading = ref(false);
const isViewSwitching = ref(false); 

const videoContainer = ref(null);
const player = ref(null);
const isVideoPlaying = ref(false);
const videoStatus = ref("播放器准备就绪");
const isPlayerReady = ref(false);
const annotationDelayTimer = ref(null);
const overlayTimer = ref(null);

// const maxRetries = 30;
// const retryCounter = ref(0);
// const retryDelay = 5000;

const switchViewMaxRetries = 3;
const switchViewRetryCounter = ref(0);
const switchViewRetryDelay = 3000; // 3秒后重试

const currentCamera = computed(() => cameras.value[currentCameraId.value]);

const views = computed(() => {
  if (!currentCamera.value) return [];
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

const formattedPopupDetails = computed(() => {
  if (!hoveredAnnotation.value || !hoveredAnnotation.value.details) {
    return '';
  }

  const lines = hoveredAnnotation.value.details.split(/\s*<\/?br.*?>\s*/);

  const processedLines = lines.map(line => {
    const trimmedLine = line.trim();
    if (trimmedLine.startsWith('开始时间:') || trimmedLine.startsWith('完成时间:')) {
      return `<span style="color: yellow;">${trimmedLine}</span>`;
    } else {
      return trimmedLine;
    }
  });

  return processedLines.filter(line => line).join('<br>');
});

// 加载label.json文件
const loadLabelData = async () => {
  if (labelData !== null) {
    return labelData; // 如果已经加载过，直接返回缓存
  }

  try {
    console.log("正在加载label.json文件...");
    const response = await fetch('/label.json');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    labelData = await response.json();
    console.log("label.json文件加载成功:", labelData);
    return labelData;
  } catch (error) {
    console.error("加载label.json文件失败:", error);
    labelData = {}; // 设置为空对象避免重复加载
    return {};
  }
};

// 计算多边形中心点的函数
const calculatePolygonCenter = (points) => {
  if (!points || points.length === 0) return { x: 0, y: 0 };
  
  let centerX = 0;
  let centerY = 0;
  
  points.forEach(point => {
    centerX += point[0];
    centerY += point[1];
  });
  
  return {
    x: centerX / points.length,
    y: centerY / points.length
  };
};

// 将label数据转换为API格式
const convertLabelToApiFormat = (labelItems, imageWidth, imageHeight, idPrefix = -1000) => {
  return labelItems.map((item, index) => {
    const center = calculatePolygonCenter(item.points);
    return {
      id: `${idPrefix + index}`,
      type: '',
      title: item.label,
      details: '',
      coordinates: [{
        x: center.x,
        y: center.y
      }],
      imageHeight: imageHeight,
      imageWidth: imageWidth,
      isFlag: true // 标记这是红旗数据
    };
  });
};

onMounted(async () => {
  await nextTick();
  
  accessToken.value = route.query.accessToken;
  currentCameraId.value = route.query.cameraName;
  currentViewId.value = route.query.view || 'view1';

  if (!accessToken.value || !currentCameraId.value) {
    videoStatus.value = "错误：缺少访问令牌或摄像头信息。";
    console.error("Missing accessToken or cameraName in URL query parameters.");
    alert("无法加载视频，缺少必要参数。");
    return;
  }
  
  initCanvas();
  window.addEventListener('resize', handleResize);

  try {
    isLoading.value = true;
    
    await initPlayer();

  } catch (error) {
    console.error("在 onMounted 期间发生错误:", error);
    videoStatus.value = `初始化失败: ${error.message}`;
  } finally {
    isLoading.value = false;
  }
});

onUnmounted(() => {
  if (player.value) {
    player.value.destroy();
  }
  if (annotationDelayTimer.value) {
    clearTimeout(annotationDelayTimer.value);
  }
  if (overlayTimer.value) {
    clearTimeout(overlayTimer.value);
  }
  window.removeEventListener('resize', handleResize);
});

const toggleCameraDrawer = () => {
  isCameraDrawerOpen.value = !isCameraDrawerOpen.value;
};

const handleGlobalClick = (event) => {
  if (isCameraDrawerOpen.value) {
    const panel = document.querySelector('.drawer-panel');
    const handle = document.querySelector('.drawer-handle');
    
    if (panel && handle && 
        !panel.contains(event.target) && 
        !handle.contains(event.target)) {
      isCameraDrawerOpen.value = false;
    }
  }
};

const initPlayer = async () => {
  isPlayerReady.value = false;
  videoStatus.value = "正在初始化播放器...";

  if (player.value) {
    await player.value.destroy();
    player.value = null;
  }

  // 等待DOM更新
  await nextTick();

  if (!videoContainer.value) {
    console.error("Video container not found in DOM");
    return;
  }
  // 为播放器创建一个唯一的容器ID
  const playerContainerId = 'video-player-' + Date.now();
  videoContainer.value.innerHTML = `<div id="${playerContainerId}" style="width: 100%; height: 100%;"></div>`;

  const camera = currentCamera.value;
  if (!camera || !camera.deviceSerial) {
    videoStatus.value = "错误：找不到当前摄像头设备。";
    return;
  }

  // 直接拼接 EZOPEN 协议地址
  const ezopenURL = `ezopen://open.ys7.com/${camera.deviceSerial}/1.live`;

  console.log(`Initializing EZUIKit player for URL: ${ezopenURL}`);

  isViewSwitching.value = true;

  // 初始化 EZUIKit 播放器
  player.value = new EZUIKit.EZUIKitPlayer({
    id: playerContainerId,
    accessToken: accessToken.value,
    url: ezopenURL,
    template: 'simple', // 使用极简模板
    quality: '0',
    autoplay: true,
    muted: true,
    audio: false,
    handleSuccess: () => {
      console.log("EZUIKit 播放成功");
      playerRetryCounter.value = 0; // 播放成功后，重置重试计数器
      isVideoPlaying.value = true;
      videoStatus.value = "视频流播放中";
      // 视频成功播放，加载当前视角的标注
      switchView(currentViewId.value, true);
    },
    handleError: (e) => {
      console.error("EZUIKit 播放错误:", e);
      isVideoPlaying.value = false;
      // videoStatus.value = `播放错误: ${e.msg || '未知错误，请刷新'}`;
      // 视频播放出错，清除所有标注
      annotations.value = [];
      drawAnnotations();

      if (playerRetryCounter.value < playerMaxRetries) {
        playerRetryCounter.value++;
        videoStatus.value = `播放失败，正在进行第 ${playerRetryCounter.value}/${playerMaxRetries} 次重试...`;
        console.log(`准备在 ${playerRetryDelay / 1000} 秒后重试...`);
        setTimeout(() => {
          initPlayer(); // 重新调用初始化函数进行重试
        }, playerRetryDelay);
      } else {
        videoStatus.value = `自动重试失败，请手动刷新或切换摄像头。`;
        console.error("已达到最大重试次数，停止重试。");
      }
    }
  });
  isPlayerReady.value = true;
};

const initCanvas = () => {
    const container = document.querySelector('.video-container');
    if (!container || !annotationCanvas.value) return;

    const { clientWidth: width, clientHeight: height } = container;

    annotationCanvas.value.width = width;
    annotationCanvas.value.height = height;
    
    annotationCtx = annotationCanvas.value.getContext('2d');
    
    drawAnnotations();
};

const handleResize = () => {
   // 原有的canvas重绘逻辑
   initCanvas();

   // 调用播放器的resize方法
   if (player.value && videoContainer.value) {
     const width = videoContainer.value.clientWidth;
     const height = videoContainer.value.clientHeight;
     player.value.resize(width, height);
     console.log(`Player resized to: ${width}x${height}`); // (可选) 用于调试
   }
};

// 绘制红旗图标
const drawFlag = (ctx, x, y, size = 20) => {
  // 保存上下文状态
  ctx.save();
  
  // 旗杆
  ctx.strokeStyle = '#8B4513'; // 棕色
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x, y - size * 1.5);
  ctx.stroke();
  
  // 旗子
  ctx.fillStyle = '#FF0000'; // 红色
  ctx.beginPath();
  ctx.moveTo(x, y - size * 1.5);
  ctx.lineTo(x + size, y - size * 1.2);
  ctx.lineTo(x + size * 0.7, y - size);
  ctx.lineTo(x, y - size * 1.2);
  ctx.closePath();
  ctx.fill();
  
  // 旗子边框
  ctx.strokeStyle = '#8B0000'; // 深红色
  ctx.lineWidth = 1;
  ctx.stroke();
  
  // 恢复上下文状态
  ctx.restore();
};

const drawAnnotations = () => {
  if (!annotationCtx) return;
  const currentCanvasWidth = annotationCtx.canvas.width;
  const currentCanvasHeight = annotationCtx.canvas.height;
  
  annotationCtx.clearRect(0, 0, currentCanvasWidth, currentCanvasHeight);

  let taizuoCounter = 1;

  // 先绘制普通标注
  annotations.value.filter(anno => !anno.isFlag).forEach(anno => {
    const color = typeColors[anno.type] || '#FFFFFF'; 
    const coordinates = anno.coordinates;

    if (!coordinates || coordinates.length < 2 || !anno.imageWidth || !anno.imageHeight) return;

    const scaleX = currentCanvasWidth / anno.imageWidth;
    const scaleY = currentCanvasHeight / anno.imageHeight;

    annotationCtx.lineWidth = 3;
    annotationCtx.strokeStyle = color;
    annotationCtx.fillStyle = `${color}4D`;

    annotationCtx.beginPath();
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

    let labelText = anno.title;
    if (anno.type === '台座') {
      labelText = `台座${taizuoCounter}`;
      taizuoCounter++;
    }

    annotationCtx.fillStyle = '#FFFFFF';
    annotationCtx.font = 'bold 16px Arial';
    annotationCtx.textBaseline = 'top';
    const textX = startX + 10;
    const textY = startY + 10;
    annotationCtx.fillText(labelText, textX, textY);
  });

  // 然后绘制红旗（确保在最上层）
  annotations.value.filter(anno => anno.isFlag).forEach(anno => {
    const coordinates = anno.coordinates;
    if (!coordinates || coordinates.length === 0 || !anno.imageWidth || !anno.imageHeight) return;

    const scaleX = currentCanvasWidth / anno.imageWidth;
    const scaleY = currentCanvasHeight / anno.imageHeight;

    const flagX = coordinates[0].x * scaleX;
    const flagY = coordinates[0].y * scaleY;
    const flagSize = 25; // 旗子大小
    
    // 1. 绘制旗子图标
    drawFlag(annotationCtx, flagX, flagY, flagSize);

    // --- 新增代码开始 ---
    // 2. 在旗子旁边绘制标题文字
    if (anno.title) {
      const labelText = anno.title;
      const textPadding = 5; // 文字与旗子之间的间距
      const textX = flagX + flagSize + textPadding; // X坐标：旗杆X + 旗子宽度 + 间距
      const textY = flagY - flagSize; // Y坐标：与旗子顶部对齐

      // 设置文字样式
      annotationCtx.fillStyle = '#FFFFFF'; // 白色文字
      annotationCtx.font = 'bold 16px Arial';
      annotationCtx.textBaseline = 'middle'; // 垂直居中对齐
      annotationCtx.textAlign = 'left'; // 水平向左对齐

      // 绘制文字
      annotationCtx.fillText(labelText, textX, textY);
    }
    // --- 新增代码结束 ---
  });
};


const fetchAnnotations = async (location, view) => {
  console.log(`正在从后台获取标注数据: ${location}, view: ${view}`);
  const url = `http://59.110.65.210:8081/label?location=${location}&view=${view}`;
  try {
    const response = await fetch(url, { method: 'GET' });
    if (!response.ok) throw new Error(`Network response was not ok (${response.status})`);
    
    const apiData = await response.json();
    console.log("API标注数据加载成功:", apiData);
    
    // 加载label.json数据
    const labelData = await loadLabelData();

    // 获取对应的label数据
    const labelKey = `${location}_${view}`;
    const labelItems = labelData[labelKey] || [];
    console.log(`找到${labelKey}对应的label数据:`, labelItems);

    // 从label数据中获取图像尺寸
    const imageWidth = labelData.imageWidth || 3840;
    const imageHeight = labelData.imageHeight || 2160;

    // 转换label数据为API格式
    const convertedLabelData = convertLabelToApiFormat(labelItems, imageWidth, imageHeight);
    console.log("转换后的label数据:", convertedLabelData);

    // 合并API数据和label数据
    const mergedData = [...apiData, ...convertedLabelData];
    console.log("合并后的数据:", mergedData);
    
    return mergedData;
  } catch (error) {
    console.error("获取标注数据失败:", error);
    return [];
  }
};

const switchCamera = async (cameraId) => {
  if (isLoading.value || currentCameraId.value === cameraId) {
    console.log(`播放器正在加载或摄像头未改变，取消切换。`);
    return;
  }

  playerRetryCounter.value = 0; // 重置重试计数器

  try {
    isCameraDrawerOpen.value = false;

    isLoading.value = true;
    console.log(`开始切换到摄像头: ${cameraId}`);
    currentCameraId.value = cameraId;
    currentViewId.value = 'view1';
    
    annotations.value = [];
    drawAnnotations();
    
    videoStatus.value = "正在切换摄像头...";

    await initPlayer();
    
    await switchView('view1', true);
    
    console.log(`摄像头切换到 ${cameraId} 完成`);
  } catch (error) {
    console.error("摄像头切换失败:", error);
    videoStatus.value = "摄像头切换失败";
  } finally {
    isLoading.value = false;
  }
};

const switchView = async (viewId, forceExecution = false, isRetry = false) => {
  // 对于用户发起的新的切换请求，重置重试计数器
  if (!isRetry) {
    switchViewRetryCounter.value = 0;
  }

   // 阻止在加载时重复点击
   if (isLoading.value && !forceExecution) {
     console.warn("系统正在加载中，请稍后再试。");
     return;
   }

   try {
     // 仅在首次尝试时设置加载状态和UI
     if (!isRetry) {
       isLoading.value = true;
       isViewSwitching.value = true;

       console.log(`准备切换到视角: ${viewId}`);
       currentViewId.value = viewId;

       if (annotationDelayTimer.value) clearTimeout(annotationDelayTimer.value);
       if (overlayTimer.value) clearTimeout(overlayTimer.value);

       annotations.value = [];
       drawAnnotations();
     }

     const indexMatch = viewId.match(/(\d+)$/);
     if (!indexMatch) throw new Error(`无效的视角ID格式: ${viewId}`);

     const index = parseInt(indexMatch[1], 10);
     const deviceSerial = currentCamera.value.deviceSerial;
     const channelNo = 1;
     const apiUrl = `https://open.ys7.com/api/lapp/device/preset/move?accessToken=${accessToken.value}&deviceSerial=${deviceSerial}&index=${index}&channelNo=${channelNo}`;

     const response = await fetch(apiUrl, { method: 'POST' });
     const result = await response.json();

     if (!response.ok || result.code !== '200') {
       throw new Error(`API 错误: ${result.msg || '未知错误'}`);
     }

     console.log(`视角 ${viewId} 切换指令发送成功。`);
     switchViewRetryCounter.value = 0; // 成功后重置计数器

     const newAnnotations = await fetchAnnotations(currentCameraId.value, viewId);
     const delayTime = 10000;

     annotationDelayTimer.value = setTimeout(() => {
       console.log("延迟结束，正在显示新标注。");
       annotations.value = newAnnotations;
       drawAnnotations();
       isViewSwitching.value = false;
       isLoading.value = false; // 整个流程成功结束，解除加载状态
     }, delayTime);

     videoStatus.value = `视频流播放中`;
   } catch (error) {
     console.error(`切换到视角 ${viewId} 失败 (尝试次数 ${switchViewRetryCounter.value + 1}):`, error);

     if (switchViewRetryCounter.value < switchViewMaxRetries) {
       switchViewRetryCounter.value++;
       videoStatus.value = `视角切换失败，正在进行第 ${switchViewRetryCounter.value}/${switchViewMaxRetries} 次重试...`;
       // 延迟后再次调用自身，并标记为重试
       setTimeout(() => {
         switchView(viewId, true, true);
       }, switchViewRetryDelay);
     } else {
       // 达到最大重试次数后，彻底失败
       videoStatus.value = `视角切换失败: ${error.message}`;
       isViewSwitching.value = false;
       isLoading.value = false; // 整个流程失败结束，解除加载状态
     }
   }
};

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

// 检查点是否在红旗附近
const isPointNearFlag = (mousePos, flagPos, tolerance = 15) => {
  const distance = Math.sqrt(
    Math.pow(mousePos.x - flagPos.x, 2) + Math.pow(mousePos.y - flagPos.y, 2)
  );
  return distance <= tolerance;
};

const handleCanvasMouseMove = (e) => {
  if (!annotationCanvas.value) return;
  const rect = annotationCanvas.value.getBoundingClientRect();
  const mousePos = { x: e.clientX - rect.left, y: e.clientY - rect.top };

  const currentCanvasWidth = annotationCanvas.value.width;
  const currentCanvasHeight = annotationCanvas.value.height;

  // 检查是否在红旗上（但不显示弹窗）
  const flagAnnotation = annotations.value.slice().reverse().find(anno => {
    if (!anno.isFlag || !anno.imageWidth || !anno.imageHeight) return false;
    const scaleX = currentCanvasWidth / anno.imageWidth;
    const scaleY = currentCanvasHeight / anno.imageHeight;
    
    const flagX = anno.coordinates[0].x * scaleX;
    const flagY = anno.coordinates[0].y * scaleY;
    
    return isPointNearFlag(mousePos, { x: flagX, y: flagY });
  });

  if (flagAnnotation) {
    // 在红旗上，显示指针但不显示弹窗
    canvasCursor.value = 'pointer';
    hoveredAnnotation.value = null;
    return;
  }

  // 检查普通标注
  const currentHover = annotations.value.slice().reverse().find(anno => {
      if (anno.isFlag || !anno.imageWidth || !anno.imageHeight) return false;
      const scaleX = currentCanvasWidth / anno.imageWidth;
      const scaleY = currentCanvasHeight / anno.imageHeight;

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

.video-container {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
}

.annotation-canvas-layer {
  position: absolute; 
  top: 0; 
  left: 0;
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

.drawer-container {
  position: absolute;
  top: 65px;
  left: 0;
  z-index: 50;
  pointer-events: auto;
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
  overflow: visible;
}
.drawer-panel.is-open {
  transform: translateX(0);
  box-shadow: 10px 0 25px rgba(0, 0, 0, 0.3);
}
.drawer-handle {
  position: absolute;
  top: 0;
  left: 100%;
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
  white-space: nowrap;
  transition: background-color 0.3s;
}
.drawer-container:hover {
  background-color: rgba(0, 191, 255, 1);
}

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

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
  backdrop-filter: blur(3px);
}

.loading-content {
  text-align: center;
  color: white;
}

.loading-spinner {
  display: inline-block;
  width: 80px;
  height: 80px;
  margin-bottom: 20px;
}

.loading-spinner:after {
  content: " ";
  display: block;
  width: 64px;
  height: 64px;
  margin: 8px;
  border-radius: 50%;
  border: 6px solid #00BFFF;
  border-color: #00BFFF transparent #00BFFF transparent;
  animation: loading-spinner 1.2s linear infinite;
}

.loading-text {
  font-size: 20px;
  font-weight: 500;
  text-shadow: 0 1px 5px rgba(0, 0, 0, 0.5);
}

@keyframes loading-spinner {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>