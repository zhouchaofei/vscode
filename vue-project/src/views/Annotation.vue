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
        <div class="loading-text">视角切换中，请稍候...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue';
import { useRoute } from 'vue-router';

import videojs from 'video.js';
import 'video.js/dist/video-js.css';

const cameras = ref({
  yn: { id: 'yn', name: '永年', url: '', viewCount: 3, deviceSerial: '33011063992677425735:33010516991327760034' },
  fx_n: { id: 'fx_n', name: '肥乡北', url: '', viewCount: 3, deviceSerial: '33011063992677425735:33010084991327588111' },
  fx_s: { id: 'fx_s', name: '肥乡南', url: '', viewCount: 3, deviceSerial: '33011063992677425735:33011012991327147072' },
  fx_lc: { id: 'fx_lc', name: '肥乡梁场', url: '', viewCount: 1, deviceSerial: '33011063992677425735:33011033991327056374' }
});

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

const maxRetries = 30;
const retryCounter = ref(0);
const retryDelay = 1000;

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
    
    await fetchAllCameraUrls(accessToken.value);
    
    const initialCamera = cameras.value[currentCameraId.value];
    if (!initialCamera || !initialCamera.url) {
        throw new Error(`无法获取摄像头 ${initialCamera.name} 的播放地址，请刷新页面。`);
    }

    await initPlayer(initialCamera.url);
    
    console.log("播放器初始化完成，加载默认视角数据。");
    await switchView(currentViewId.value, true);

  } catch (error) {
    console.error("在 onMounted 期间发生错误:", error);
    videoStatus.value = `初始化失败: ${error.message}`;
  } finally {
    isLoading.value = false;
  }
});

onUnmounted(() => {
  if (player.value) {
    player.value.dispose();
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

const fetchAllCameraUrls = async (token) => {
    console.log("Annotation page fetching camera URLs...");
    const url = 'https://open.ys7.com/api/lapp/v2/live/address/get';
    
    const promises = Object.values(cameras.value).map(async (camera) => {
      const params = new URLSearchParams();
      params.append('accessToken', token);
      params.append('deviceSerial', camera.deviceSerial);
      params.append('channelNo', 1);
      params.append('protocol', 2);

      try {
          const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: params
          });
          const data = await response.json();
          if (data.code === '200' && data.data) {
            camera.url = data.data.url;
          } else {
            console.error(`Failed to get URL for ${camera.name}: ${data.msg}`);
          }
      } catch (error) {
          console.error(`Network error fetching URL for ${camera.name}:`, error);
      }
    });

    await Promise.all(promises);
    console.log("All camera URL fetch requests completed for annotation page.");
};

const handlePlaybackErrorAndRetry = async () => {
    try {
        console.log("Re-fetching camera URL for recovery...");
        videoStatus.value = "正在重新获取播放地址...";

        const cameraToRetry = cameras.value[currentCameraId.value];
        const token = accessToken.value;
        const url = 'https://open.ys7.com/api/lapp/v2/live/address/get';
        const params = new URLSearchParams();
        params.append('accessToken', token);
        params.append('deviceSerial', cameraToRetry.deviceSerial);
        params.append('channelNo', 1);
        params.append('protocol', 2);

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: params
        });
        const data = await response.json();

        if (data.code === '200' && data.data && data.data.url) {
            const newUrl = data.data.url;
            console.log("Successfully fetched new URL. Re-initializing player.");
            cameras.value[currentCameraId.value].url = newUrl;
            await initPlayer(newUrl);
            retryCounter.value = 0;
        } else {
            throw new Error(`Failed to get new URL: ${data.msg}`);
        }
    } catch (error) {
        console.error("Retry attempt failed:", error);
        videoStatus.value = "自动重试失败。请手动刷新。";
    }
};

const initPlayer = (url) => {
  return new Promise((resolve, reject) => {
    isPlayerReady.value = false;
    videoStatus.value = "正在初始化播放器...";
    
    if (player.value) {
      player.value.dispose();
      player.value = null;
    }
    
    nextTick(() => {
      if (!videoContainer.value) {
        return reject(new Error("Video container not found in DOM"));
      }
      
      const videoElement = document.createElement('video');
      videoElement.className = 'video-js vjs-default-skin';
      videoElement.id = 'video-player-' + Date.now(); // 唯一ID
      
      videoContainer.value.innerHTML = '';
      videoContainer.value.appendChild(videoElement);
      
      try {
        const options = {
          autoplay: true,
          muted: true,
          controls: true,
          preload: 'auto',
          responsive: true,
          sources: [{ 
            src: url, 
            type: 'application/x-mpegURL' 
          }]
        };

        player.value = videojs(videoElement, options, function() {
          console.log('Video.js 播放器已创建并准备就绪');
          this.on('playing', () => { 
            isVideoPlaying.value = true; 
            videoStatus.value = "视频流播放中"; 
            retryCounter.value = 0;
          });
          
          this.on('error', (e) => {
            const error = this.error() || e;
            isVideoPlaying.value = false;
            console.error('Video.js Error:', error);

            if (error && error.code === 3 && retryCounter.value < maxRetries) {
                retryCounter.value++;
                videoStatus.value = `视频流中断，正在进行第 ${retryCounter.value} 次自动重试...`;
                console.log(`Playback error detected. Attempting retry ${retryCounter.value}/${maxRetries}...`);
                setTimeout(handlePlaybackErrorAndRetry, retryDelay);
            } else if (retryCounter.value >= maxRetries) {
                videoStatus.value = "自动重试失败，请手动刷新或切换摄像头。";
                console.error("Maximum retries reached. Aborting.");
            } else {
                videoStatus.value = `播放错误: ${error?.message || '未知错误'}`;
            }
          });
          
          this.on('ended', () => { 
            isVideoPlaying.value = false; 
            videoStatus.value = '播放结束'; 
          });
          
          this.on('pause', () => { 
            isVideoPlaying.value = false; 
            videoStatus.value = '已暂停'; 
          });
          
          this.play().catch(error => {
            console.warn("自动播放被浏览器阻止:", error);
          });
          
          resolve();
        });
      } catch (error) {
        console.error("创建播放器实例失败:", error);
        reject(error);
      }
    });
  });
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
    initCanvas();
};

const drawAnnotations = () => {
  if (!annotationCtx) return;
  const currentCanvasWidth = annotationCtx.canvas.width;
  const currentCanvasHeight = annotationCtx.canvas.height;
  
  annotationCtx.clearRect(0, 0, currentCanvasWidth, currentCanvasHeight);

  let taizuoCounter = 1;

  annotations.value.forEach(anno => {
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
};


const fetchAnnotations = async (location, view) => {
  console.log(`正在从后台获取标注数据: ${location}, view: ${view}`);
  const url = `http://59.110.65.210:8081/label?location=${location}&view=${view}`;
  try {
    const response = await fetch(url, { method: 'GET' });
    if (!response.ok) throw new Error(`Network response was not ok (${response.status})`);
    
    const data = await response.json();
    console.log("标注数据加载成功:", data);
    return data;
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

  try {
    isCameraDrawerOpen.value = false;

    isLoading.value = true;
    console.log(`开始切换到摄像头: ${cameraId}`);
    currentCameraId.value = cameraId;
    currentViewId.value = 'view1';
    
    annotations.value = [];
    drawAnnotations();
    
    videoStatus.value = "正在切换摄像头...";

    const newCamera = cameras.value[cameraId];
    if (!newCamera.url) {
        throw new Error(`URL for ${newCamera.name} is not available.`);
    }

    await initPlayer(newCamera.url);
    
    await switchView('view1', true);
    
    console.log(`摄像头切换到 ${cameraId} 完成`);
  } catch (error) {
    console.error("摄像头切换失败:", error);
    videoStatus.value = "摄像头切换失败";
  } finally {
    isLoading.value = false;
  }
};

const switchView = async (viewId, forceExecution = false) => {
  if (isLoading.value && !forceExecution) {
    console.warn("系统正在加载中，请稍后再试。");
    return;
  }

  try {
    if (!forceExecution) {
      isLoading.value = true;
    }

    isViewSwitching.value = true;
    
    console.log(`准备切换到视角: ${viewId}`);
    currentViewId.value = viewId;

    if (annotationDelayTimer.value) {
      clearTimeout(annotationDelayTimer.value);
    }
    if (overlayTimer.value) {
      clearTimeout(overlayTimer.value);
    }

    annotations.value = [];
    drawAnnotations();

    const indexMatch = viewId.match(/(\d+)$/);
    if (!indexMatch) {
      throw new Error(`无效的视角ID格式: ${viewId}`);
    }
    
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
    
    const newAnnotations = await fetchAnnotations(currentCameraId.value, viewId);
    
    const delayTime = 20000;

    annotationDelayTimer.value = setTimeout(() => {
      console.log("延迟结束，正在显示新标注。");
      annotations.value = newAnnotations;
      drawAnnotations();
      isViewSwitching.value = false;
    }, delayTime);
    
  } catch (error) {
    console.error(`切换到视角 ${viewId} 失败:`, error);
    videoStatus.value = `视角切换失败: ${error.message}`;
    isViewSwitching.value = false;
  } finally {
    isLoading.value = false;
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

const handleCanvasMouseMove = (e) => {
  if (!annotationCanvas.value) return;
  const rect = annotationCanvas.value.getBoundingClientRect();
  const mousePos = { x: e.clientX - rect.left, y: e.clientY - rect.top };

  const currentCanvasWidth = annotationCanvas.value.width;
  const currentCanvasHeight = annotationCanvas.value.height;

  const currentHover = annotations.value.slice().reverse().find(anno => {
      if (!anno.imageWidth || !anno.imageHeight) return false;
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

.video-container :deep(.video-js) {
    width: 100%;
    height: 100%;
}

.video-container :deep(.video-js .vjs-tech) {
  object-fit: fill;
}

.video-container :deep(.video-js .vjs-control-bar) {
  display: none;
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