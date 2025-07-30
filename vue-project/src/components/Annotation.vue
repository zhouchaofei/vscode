<template>
  <div class="annotator-container" @click="handleGlobalClick">
    <div ref="videoContainer" class="video-container">
      <!-- 动态创建视频元素 -->
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
            <!-- 动态生成摄像头按钮 -->
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
          <!-- 动态生成视图按钮 -->
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
          <p v-html="hoveredAnnotation.details.replace(/\|/g, '<br>')"></p>
        </div>
      </main>
    </div>

    <!-- 视角切换加载蒙层 -->
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

// 新增：静态的人员数据（写死）
const personnelData = ref({
  total: 0,           // 施工人员总数
  safetyAlerts: 0      // 无安全帽佩戴提醒次数
});

// 不同标注类型的颜色映射
const typeColors = {
  // 结构与主要组件 (暖色调)
  '盖梁': '#FF8C00',      // 暗橙色 (DarkOrange)
  '箱梁': '#FFA500',      // 橙色 (Orange)
  '桥墩': '#FFD700',      // 金色 (Gold)
  '桥台': '#F0E68C',      // 卡其色 (Khaki)
  '预制梁': '#FF6347',    // 番茄红 (Tomato)
  '跨': '#CD853F',        // 新增: 秘鲁色 (Peru)

  // 交通与设施 (醒目的颜色)
  '方向': '#FF4500',      // 橙红色 (OrangeRed)
  '匝道': '#1E90FF',      // 道奇蓝 (DodgerBlue)
  '通道': '#32CD32',      // 酸橙绿 (LimeGreen)
  '收费站': '#9370DB',    // 新增: 中紫色 (MediumPurple)

  // 支撑与细节部件 (冷色/中性色)
  '支座': '#00FFFF',      // 青色 (Aqua/Cyan)
  '挡块': '#B0C4DE',      // 亮钢蓝 (LightSteelBlue)
  '涵洞': '#9932CC',      // 暗兰花紫 (DarkOrchid)
  '台座': '#D2B48C',      // 新增: 黄褐色 (Tan)
  '路肩墙': '#708090',    // 新增: 石板灰 (SlateGray)

  // 其他
  '其他': '#FFFFFF'       // 白色 (White)
};

// --- 状态管理 ---
// --- Canvas 和状态管理 ---
const annotationCanvas = ref(null);
let annotationCtx = null;

const annotations = ref([]); // 保存来自后端的标注数据
const hoveredAnnotation = ref(null); // 保存当前鼠标悬停的标注
const popupPosition = ref({ x: 0, y: 0 }); // 详情弹出框的位置
const canvasCursor = ref('default'); // 用于在悬停时将光标变为'pointer'

const route = useRoute();

// --- 摄像头和视角状态 ---
const currentCameraId = ref('yn'); // 默认选中'永年'摄像头
const currentViewId = ref('view1'); // 默认选中视角1
const isCameraDrawerOpen = ref(false); // 控制抽屉状态
const isLoading = ref(false); // 加载状态标记
const isViewSwitching = ref(false); // 新增：视角切换蒙层状态

// --- Video.js 播放器状态 ---
const videoContainer = ref(null); // 视频容器的引用
const videoPlayer = ref(null);    // 视频元素的引用
const player = ref(null);      // 用于持有 Video.js 播放器实例
const isVideoPlaying = ref(false);
const videoStatus = ref("播放器准备就绪");
const isPlayerReady = ref(false); // 状态锁，标记播放器是否准备就绪
const annotationDelayTimer = ref(null);
const overlayTimer = ref(null); // 用于控制蒙层显示时长的计时器

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
// onMounted 现在是 async 函数
onMounted(async () => {
  // 确保 DOM 已经渲染
  await nextTick();
  
  // 从URL获取参数
  currentCameraId.value = route.query.cameraName;
  currentViewId.value = route.query.view;
  // currentCamera.value = cameras.value[currentCameraId.value];
  console.log(`从URL获取的摄像头名称: ${currentCameraId.value}, 视角: ${currentViewId.value}`);
  console.log(`当前摄像头数据:`, currentCamera.value);
  
  initCanvas();
  window.addEventListener('resize', handleResize);

  // 等待播放器初始化完成后，再执行后续逻辑
  try {
    isLoading.value = true;
    await initPlayer(currentCamera.value.url);
    console.log("播放器初始化流程完成，现在开始加载默认视角数据。");
    // 初始加载：切换到默认摄像头和视角
    await switchView(currentViewId.value, true);
  } catch (error) {
    console.error("在 onMounted 期间初始化播放器失败:", error);
    videoStatus.value = "播放器初始化失败";
  } finally {
    isLoading.value = false;
  }
});

onUnmounted(() => {
  // 销毁播放器以释放资源
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

// --- 摄像头面板交互 ---
// 切换摄像头抽屉的显示状态
const toggleCameraDrawer = () => {
  isCameraDrawerOpen.value = !isCameraDrawerOpen.value;
};

// 处理全局点击事件，检测点击是否在面板外
const handleGlobalClick = (event) => {
  if (isCameraDrawerOpen.value) {
    // 检查点击是否在抽屉面板内
    const panel = document.querySelector('.drawer-panel');
    const handle = document.querySelector('.drawer-handle');
    
    if (panel && handle && 
        !panel.contains(event.target) && 
        !handle.contains(event.target)) {
      isCameraDrawerOpen.value = false;
    }
  }
};

// --- Video.js 播放器初始化 ---
/**
 * 修复版的初始化 Video.js 播放器函数
 * 动态创建视频元素而不是尝试重用
 */
const initPlayer = (initialUrl) => {
  return new Promise((resolve, reject) => {
    isPlayerReady.value = false;
    videoStatus.value = "正在初始化播放器...";
    
    // 先清除旧播放器实例
    if (player.value) {
      try {
        player.value.dispose();
        player.value = null;
      } catch (e) {
        console.warn("销毁旧播放器时发生错误:", e);
      }
    }
    
    // 使用 nextTick 确保 DOM 已更新
    nextTick(() => {
      // 检查视频容器是否存在
      if (!videoContainer.value) {
        return reject(new Error("Video container not found in DOM"));
      }
      
      // 创建全新的视频元素
      const videoElement = document.createElement('video');
      videoElement.className = 'video-js vjs-default-skin';
      videoElement.id = 'video-player-' + Date.now(); // 唯一ID
      
      // 清空容器并添加新元素
      videoContainer.value.innerHTML = '';
      videoContainer.value.appendChild(videoElement);
      
      // 保存新的引用
      videoPlayer.value = videoElement;
      
      try {
        // 创建播放器配置
        const options = {
          autoplay: true,
          muted: true,
          controls: true,
          preload: 'auto',
          responsive: true,
          sources: [{ 
            src: initialUrl, 
            type: 'application/x-mpegURL' 
          }]
        };

        // 创建新的播放器实例
        player.value = videojs(videoElement, options, function() {
          console.log('Video.js 播放器已创建并准备就绪');
          isPlayerReady.value = true;

          // 设置各种事件监听器
          this.on('playing', () => { 
            isVideoPlaying.value = true; 
            videoStatus.value = "视频流播放中"; 
          });
          
          this.on('error', (e) => {
            const error = this.error() || e;
            isVideoPlaying.value = false;
            videoStatus.value = `播放错误: ${error?.message || '未知错误'}`;
            console.error('Video.js Error:', error);
          });
          
          this.on('ended', () => { 
            isVideoPlaying.value = false; 
            videoStatus.value = '播放结束'; 
          });
          
          this.on('pause', () => { 
            isVideoPlaying.value = false; 
            videoStatus.value = '已暂停'; 
          });
          
          // 尝试播放
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
  const url = `http://59.110.65.210:8081/label?location=${location}&view=${view}`;
  try {
    const response = await fetch(url, { method: 'GET' });
    if (!response.ok) throw new Error(`Network response was not ok (${response.status})`);
    
    const data = await response.json();
    console.log("标注数据加载成功:", data);
    return data; // 返回加载的标注数据
  } catch (error) {
    console.error("获取标注数据失败:", error);
    return [];
  }
};

/**
 * 切换摄像头 - 完全销毁和重建播放器
 */
const switchCamera = async (cameraId) => {
  if (isLoading.value || currentCameraId.value === cameraId) {
    console.log(`播放器正在加载或摄像头未改变，取消切换。`);
    return;
  }

  try {
    // 选择摄像头后关闭面板
    isCameraDrawerOpen.value = false;

    isLoading.value = true;
    console.log(`开始切换到摄像头: ${cameraId}`);
    currentCameraId.value = cameraId;
    currentViewId.value = 'view1'; // 重置为默认视角
    
    // 清除所有标注
    annotations.value = [];
    drawAnnotations();
    
    // 更新状态
    isVideoPlaying.value = false;
    videoStatus.value = "正在切换摄像头...";

    // 完全重新初始化播放器
    await initPlayer(cameras.value[cameraId].url);
    
    // 切换到默认视角并加载标注
    await switchView('view1', true);
    
    console.log(`摄像头切换到 ${cameraId} 完成`);
  } catch (error) {
    console.error("摄像头切换失败:", error);
    videoStatus.value = "摄像头切换失败";
  } finally {
    isLoading.value = false;
  }
};

/**
 * 修复版的切换视角函数
 * @param {string} viewId - 要切换到的视角ID
 * @param {boolean} forceExecution - 即使系统正在加载也强制执行
 */
const switchView = async (viewId, forceExecution = false) => {
  // 如果系统正在加载且不是强制执行，则直接返回
  if (isLoading.value && !forceExecution) {
    console.warn("系统正在加载中，请稍后再试。");
    return;
  }

  try {
    // 只有当不是强制执行时才设置加载状态
    // 这避免了在初始化或摄像头切换期间的重复加载状态
    if (!forceExecution) {
      isLoading.value = true;
    }

    // 显示视角切换蒙层
    isViewSwitching.value = true;
    
    console.log(`准备切换到视角: ${viewId}`);
    currentViewId.value = viewId; // 更新当前视角状态

    if (annotationDelayTimer.value) {
      clearTimeout(annotationDelayTimer.value);
    }
    if (overlayTimer.value) {
      clearTimeout(overlayTimer.value);
    }

    // 清除当前标注
    annotations.value = [];
    drawAnnotations();

    // 预设点切换逻辑
    const indexMatch = viewId.match(/(\d+)$/);
    if (!indexMatch) {
      throw new Error(`无效的视角ID格式: ${viewId}`);
    }
    
    const index = parseInt(indexMatch[1], 10);
    const accessToken = "at.clyk2nli5ca2q6ci1mjfaxnlc5ta6jhh-5mo44wo80f-111mhjh-qbpvdn0vj";
    const deviceSerial = currentCamera.value.deviceSerial;
    const channelNo = 1;
    const apiUrl = `https://open.ys7.com/api/lapp/device/preset/move?accessToken=${accessToken}&deviceSerial=${deviceSerial}&index=${index}&channelNo=${channelNo}`;

    // 发送视角切换指令
    const response = await fetch(apiUrl, { method: 'POST' });
    const result = await response.json();

    // 萤石云API成功响应码为'200'
    if (!response.ok || result.code !== '200') {
      throw new Error(`API 错误: ${result.msg || '未知错误'}`);
    }

    console.log(`视角 ${viewId} 切换指令发送成功。`);
    
    // 获取新标注数据
    const newAnnotations = await fetchAnnotations(currentCameraId.value, viewId);
    
    // 延迟显示标注（给摄像头移动时间）
    const delayTime = 20000; // 20秒延迟
    console.log(`将在${delayTime/1000}秒后显示新标注。`);

    // 设置定时器以显示标注和隐藏蒙层
    annotationDelayTimer.value = setTimeout(() => {
      console.log("延迟结束，正在显示新标注。");
      annotations.value = newAnnotations;
      drawAnnotations();
      isViewSwitching.value = false; // 隐藏蒙层
    }, delayTime);
    
  } catch (error) {
    console.error(`切换到视角 ${viewId} 失败:`, error);
    videoStatus.value = `视角切换失败: ${error.message}`;
    isViewSwitching.value = false; // 出错时也要隐藏蒙层
  } finally {
    isLoading.value = false;
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

/* --- 让 Video.js 自己处理尺寸 --- */
.video-container :deep(.video-js) {
    width: 100%;
    height: 100%;
}

/* video.js 内部的 video 元素拉伸填充 */
.video-container :deep(.video-js .vjs-tech) {
  object-fit: fill;
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
.drawer-container:hover {
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

/* --- 加载蒙层样式 --- */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  z-index: 1000; /* 确保在所有元素之上 */
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