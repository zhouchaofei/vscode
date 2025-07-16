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
            <button @click="switchCamera('yongnian')" class="control-btn" :class="{ selected: currentCamera === 'yongnian' }">永年</button>
            <button @click="switchCamera('feixiang_south')" class="control-btn" :class="{ selected: currentCamera === 'feixiang_south' }">肥乡南</button>
            <button @click="switchCamera('feixiang_north')" class="control-btn" :class="{ selected: currentCamera === 'feixiang_north' }">肥乡北</button>
            <button @click="switchCamera('feixiang_liangchang')" class="control-btn" :class="{ selected: currentCamera === 'feixiang_liangchang' }">肥乡梁厂</button>
          </div>
          <div class="drawer-handle">
            <span>摄<br>像<br>头</span>
          </div>
        </div>
      </div>

      <div class="top-controls-container">
        <div class="controls-group view-controls">
          <button @click="switchView('view_1')" class="control-btn" :class="{ selected: currentView === 'view_1' }">视角1</button>
          <button @click="switchView('view_2')" class="control-btn" :class="{ selected: currentView === 'view_2' }">视角2</button>
          <button @click="switchView('view_3')" class="control-btn" :class="{ selected: currentView === 'view_3' }">视角3</button>
          <button @click="switchView('view_4')" class="control-btn" :class="{ selected: currentView === 'view_4' }">视角4</button>
          <button @click="switchView('view_5')" class="control-btn" :class="{ selected: currentView === 'view_5' }">视角5</button>
          <button @click="switchView('view_6')" class="control-btn" :class="{ selected: currentView === 'view_6' }">视角6</button>
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
import { ref, onMounted, onUnmounted, nextTick } from 'vue';

// --- 新增：导入 Video.js 及其 HLS 插件 ---
import videojs from 'video.js';
import 'video.js/dist/video-js.css'; // 导入 Video.js 的 CSS

// HLS 插件在导入时会自动注册
// import 'videojs-contrib-hls';  // <--- 关键！把这一行删除或注释掉！

// --- Canvas 和状态管理 ---
// const videoCanvas = ref(null); // 已移除
const annotationCanvas = ref(null);
// let videoCtx = null; // 已移除
let annotationCtx = null;

const annotations = ref([]); // 保存来自后端的标注数据
const hoveredAnnotation = ref(null); // 保存当前鼠标悬停的标注
const popupPosition = ref({ x: 0, y: 0 }); // 详情弹出框的位置
const canvasCursor = ref('default'); // 用于在悬停时将光标变为'pointer'

// --- 摄像头和视角状态 ---
const currentCamera = ref('yongnian'); // 默认选中'永年'摄像头
const currentView = ref('view_1'); // 默认选中视角1
const isCameraDrawerOpen = ref(false); // 控制抽屉状态

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

// --- 新增：Video.js 播放器状态 ---
const videoPlayer = ref(null); // 用于 <video> 元素的模板引用
const player = ref(null);      // 用于持有 Video.js 播放器实例
const isVideoPlaying = ref(false);
const videoStatus = ref("播放器准备就绪");
// --- 新增：初始视频流 URL ---
const initialStreamUrl = ref("https://open.ys7.com/v3/openlive/33011063992677425735:33010516991327760034_1_1.m3u8?expire=1783780175&id=865721859495178240&t=56c5d646f2000d3068fcd86b3c12aac95db0126db0944127dace5b10b5be4268&ev=100&devProto=gb28181");

// --- 组件生命周期钩子 ---
onMounted(() => {
  // 确保 DOM 已经渲染
  nextTick(() => {
    initCanvas();
    initPlayer(initialStreamUrl.value); // 新增：初始化 Video.js
    fetchAnnotations(); // 组件加载时获取标注
    window.addEventListener('resize', handleResize);
    // 在组件加载时，主动调用切换到默认视角1的指令
    switchView(currentView.value); 
  });
  
});

onUnmounted(() => {
  // 新增：销毁播放器以释放资源
  if (player.value) {
    player.value.dispose();
  }
  window.removeEventListener('resize', handleResize);
});

// --- 新增：Video.js 播放器初始化 ---
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
    fluid: true,       // 播放器将占满容器宽度，并保持宽高比
    responsive: true,
    sources: [{
      // 这里使用你提供的 HLS 地址作为默认视频源
      src: initialUrl,
      type: 'application/x-mpegURL' // HLS 视频流类型
    }]
  };

  player.value = videojs(videoPlayer.value, options, () => {
    if (!player.value) {
      console.error("播放器尚未初始化！");
      return;
    }
    console.log('Video.js player is ready');
    player.value.play().catch(error => {
      console.error("自动播放被浏览器阻止:", error);
      videoStatus.value = "点击播放以开始";
    });
    // 设置初始视频流
    // const initialStreamUrl = "https://open.ys7.com/v3/openlive/33011063992677425735:33011012991327147072_1_1.m3u8?expire=1783736336&id=865537983230619648&t=65b4a06c2353dc75ffe3cacdf3bec82c97b6b0c08b088414f3f88d566f4d4b1d&ev=100&devProto=gb28181";
    // setVideoStream(initialStreamUrl);
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
    videoStatus.value = `播放错误: ${error.message}`;
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

    const { clientWidth: width, clientHeight: height } = container;

    annotationCanvas.value.width = width;
    annotationCanvas.value.height = height;
    
    annotationCtx = annotationCanvas.value.getContext('2d');
    
    drawAnnotations(); // 窗口大小调整时重绘标注
};

// 优化了handleResize，现在只进行重绘，不再重新获取数据
const handleResize = () => {
    initCanvas(); // initCanvas 会重设画布大小并调用 drawAnnotations
}

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

    // 核心修改：计算缩放比例
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
const fetchAnnotations = async () => {
  console.log("正在从后台获取标注数据...");
  try {
    // 这里是你进行真实API调用的地方。
    // const response = await fetch('/api/get_annotations_for_view', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ viewId: 'current_view' }) // 如果需要，可以发送当前视图的上下文
    // });
    // if (!response.ok) throw new Error('网络响应失败');
    // const data = await response.json();

    // 为演示目的，此处使用模拟数据 (MOCK DATA)
    const mockData = [
      { id: "anno_001", type: "方向", title: "北京方向", details: "", coordinates: [{ "x": 803.06, "y": 934.55 }, { "x": 861.69, "y": 887.43 }, { "x": 848.08, "y": 883.76 }, { "x": 879.5, "y": 874.86 }, { "x": 876.88, "y": 894.76 }, { "x": 867.13, "y": 889.75 }, { "x": 808.12, "y": 938.86 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_002", type: "方向", title: "香港方向", details: "", coordinates: [{ "x": 767.34, "y": 816.66 }, { "x": 730.54, "y": 829.86 }, { "x": 726.02, "y": 824.30 }, { "x": 710.40, "y": 843.40 }, { "x": 738.87, "y": 843.05 }, { "x": 734.01, "y": 836.80 }, { "x": 772.55, "y": 822.91 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_003", type: "匝道", title: "E匝道", details: "", coordinates: [{ "x": 3.58, "y": 870.80 }, { "x": 45.92, "y": 868.61 }, { "x": 97.74, "y": 867.88 }, { "x": 161.98, "y": 868.61 }, { "x": 202.85, "y": 870.80 }, { "x": 230.59, "y": 883.94 }, { "x": 248.84, "y": 910.21 }, { "x": 260.52, "y": 932.84 }, { "x": 1.97, "y": 1005.45 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_004", type: "匝道", title: "B匝道", details: "", coordinates: [{ "x": 1582.38, "y": 1268.53 }, { "x": 1930.46, "y": 1287.76 }, { "x": 2195.84, "y": 1299.30 }, { "x": 2517.0, "y": 1287.76 }, { "x": 2558.0, "y": 1282.17 }, { "x": 2558.0, "y": 1168.53 }, { "x": 2449.69, "y": 1180.07 }, { "x": 2295.84, "y": 1178.15 }, { "x": 2151.61, "y": 1176.23 }, { "x": 1917.0, "y": 1174.30 }, { "x": 1638.15, "y": 1168.53 }, { "x": 1451.61, "y": 1147.38 }, { "x": 1251.61, "y": 1089.69 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_005", type: "桥墩", title: "1#桥墩", details: "", coordinates: [{ "x": 179.63, "y": 786.27 }, { "x": 180.13, "y": 827.34 }, { "x": 226.54, "y": 828.01 }, { "x": 228.21, "y": 785.77 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_006", type: "桥墩", title: "2#桥墩", details: "", coordinates: [{ "x": 394.25, "y": 800.78 }, { "x": 392.28, "y": 845.93 }, { "x": 433.66, "y": 842.32 }, { "x": 433.82, "y": 796.34 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_007", type: "盖梁", title: "2#盖梁", details: "", coordinates: [{ "x": 375.86, "y": 769.74 }, { "x": 376.35, "y": 795.03 }, { "x": 442.69, "y": 791.91 }, { "x": 442.20, "y": 764.98 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_008", type: "桥墩", title: "5#桥墩", details: "", coordinates: [{ "x": 1098.36, "y": 802.10 }, { "x": 1096.57, "y": 869.09 }, { "x": 1116.41, "y": 864.37 }, { "x": 1118.19, "y": 798.84 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_009", type: "桥墩", title: "6#桥墩", details: "", coordinates: [{ "x": 1346.67, "y": 820.42 }, { "x": 1345.21, "y": 869.09 }, { "x": 1365.11, "y": 879.57 }, { "x": 1366.56, "y": 814.45 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_010", type: "桥墩", title: "7#桥墩", details: "", coordinates: [{ "x": 1504.15, "y": 832.40 }, { "x": 1502.77, "y": 881.80 }, { "x": 1544.88, "y": 876.94 }, { "x": 1545.23, "y": 824.26 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_011", type: "盖梁", title: "7#盖梁", details: "", coordinates: [{ "x": 1499.48, "y": 812.82 }, { "x": 1497.22, "y": 830.67 }, { "x": 1552.51, "y": 821.49 }, { "x": 1550.95, "y": 805.02 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_012", type: "桥墩", title: "8#桥墩", details: "", coordinates: [{ "x": 1668.13, "y": 856.60 }, { "x": 1667.92, "y": 896.43 }, { "x": 1714.25, "y": 892.45 }, { "x": 1711.32, "y": 848.84 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_013", type: "盖梁", title: "8#盖梁", details: "", coordinates: [{ "x": 1660.58, "y": 836.26 }, { "x": 1658.70, "y": 854.71 }, { "x": 1724.52, "y": 845.91 }, { "x": 1721.17, "y": 827.25 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_014", type: "桥墩", title: "9#桥墩", details: "", coordinates: [{ "x": 1832.95, "y": 856.91 }, { "x": 1830.44, "y": 903.77 }, { "x": 1891.44, "y": 904.08 }, { "x": 1893.65, "y": 850.31 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_015", type: "桥墩", title: "10#桥墩", details: "", coordinates: [{ "x": 1994.0, "y": 875.66 }, { "x": 1993.0, "y": 911.0 }, { "x": 2097.33, "y": 913.0 }, { "x": 2097.33, "y": 864.0 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_016", type: "桥台", title: "11#桥台", details: "", coordinates: [{ "x": 2118.60, "y": 895.27 }, { "x": 2118.21, "y": 930.54 }, { "x": 2250.0, "y": 930.15 }, { "x": 2248.06, "y": 885.97 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_017", type: "盖梁", title: "1#盖梁", details: "", coordinates: [{ "x": 171.20, "y": 765.02 }, { "x": 171.20, "y": 784.37 }, { "x": 238.68, "y": 781.93 }, { "x": 238.84, "y": 761.61 }], imageHeight: 1439, imageWidth: 2559 },
      { id: "anno_018", type: "涵洞", title: "1-2×2m箱型涵洞CK0+310", details: "", coordinates: [{ "x": 2257.78, "y": 935.50 }, { "x": 2254.28, "y": 974.98 }, { "x": 2371.82, "y": 1009.19 }, { "x": 2374.01, "y": 955.68 }], imageHeight: 1439, imageWidth: 2559 }
    ];
    annotations.value = mockData;
    console.log("标注数据加载成功:", annotations.value);
    drawAnnotations(); // 绘制新获取的标注
  } catch (error) {
    console.error("获取标注数据失败:", error);
    alert("无法加载标注数据，请检查后台连接。");
  }
};

/**
 * NEW: 切换摄像头的预留函数
 * @param {string} cameraId - 要切换到的摄像头ID
 */
const switchCamera = async (cameraId) => {
  console.log(`指令: 切换到摄像头: ${cameraId}`);
  currentCamera.value = cameraId;
  // 此处为未来实现具体摄像头切换逻辑的预留位置。
  // 例如，这可能会关闭当前的WebSocket连接，
  // 然后使用新的URL（与cameraId关联）重新建立连接。
  alert(`已发送指令切换到 "${cameraId}"! (功能待实现)`);
  // 切换摄像头后，可能需要获取与新摄像头关联的标注
  // TODO: 当准备好后，可在此实现获取新摄像头流URL的逻辑
  // 并调用 setVideoStream(newUrl);
  // await fetchAnnotationsForCamera(cameraId);
};

/**
 * 通过向后端发送命令来切换视图。
 * 这通常会触发视频流的更改和一套新的标注。
 * CHANGE: 通过向萤石云API发送命令来切换设备预设点（视角）。
 * @param {string} viewId - 要切换到的视图ID (例如 'view_1')。
 */
// 变更：此函数现在也会更新视频播放器的源
const switchView = async (viewId) => {
  console.log(`准备切换到视角: ${viewId}`);
  currentView.value = viewId; // 更新当前视角状态

  // 从 'view_1' 中提取数字索引
  const indexMatch = viewId.match(/_(\d+)$/);
  if (!indexMatch) {
    console.error(`无效的视角ID格式: ${viewId}`);
    alert(`视角ID "${viewId}" 格式不正确。`);
    return;
  }
  const index = parseInt(indexMatch[1], 10);
  
  // 注意：这将调用萤石云API来移动摄像头。
  // 警告: accessToken 通常具有时效性，不应硬编码在前端。
  // 在生产环境中，应由后端服务器管理和提供。
  // 我们将假设流URL保持不变，因为是流内容本身发生了变化。
  // 如果每个预设点都有一个*不同*的M3U8 URL，您需要在此处更新它。
  const accessToken = "at.clyk2nli5w0duq3maaab3lr5a6s64kdh-1ovqb7s4pd-07h49dz-jxbkxlnby";
  const deviceSerial = "33011063992677425735:33010516991327760034";
  const channelNo = 1;
  const apiUrl = `https://open.ys7.com/api/lapp/device/preset/move?accessToken=${accessToken}&deviceSerial=${deviceSerial}&index=${index}&channelNo=${channelNo}`;

  try {
    const response = await fetch(apiUrl, { method: 'POST' });
    const result = await response.json();
    const timestamp = new Date().toLocaleTimeString();

    // 萤石云API成功响应码为'200'
    if (response.ok && result.code === '200') {
      console.log(`[${timestamp}] 视角切换成功 (${response.status}):`, result);
      // 成功切换视角后，可以获取新视角的标注
      // await fetchAnnotations(); 
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
    popupPosition.value.x = Math.min(mousePos.x + 15, rect.width - 220); 
    popupPosition.value.y = Math.min(mousePos.y + 15, rect.height - 100); 
    canvasCursor.value = 'pointer';
  } else {
    hoveredAnnotation.value = null;
    canvasCursor.value = 'default';
  }
};

// --- 已移除：所有与 WebSocket 相关的功能 (connectWebSocket, handleDisconnect, displayFrame, 等) ---

</script>

<style scoped>
.annotator-container {
  position: relative; width: 100vw; height: 100vh;
  background-color: #000; overflow: hidden;
  font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* --- 新增：用于容纳播放器的视频容器 --- */
.video-container {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
}

/* --- 变更：让 Video.js 自己处理尺寸 --- */
.video-js {
    width: 100%;
    height: 100%;
}

.annotation-canvas-layer {
  position: absolute; top: 0; left: 0;
  /* 变更：尺寸现在由 initCanvas 处理，但要确保它在视频之上 */
  width: 100%; height: 100%;
  z-index: 3;
}

.ui-overlay {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  z-index: 4; pointer-events: none; display: flex; flex-direction: column;
}

.main-content { flex-grow: 1; position: relative; }

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
  position: absolute; left: 50%; top: 50%;
  transform: translate(-50%, -50%);
  font-size: 2.5rem;
  font-weight: 600;
}
.connection-status {
  position: absolute; right: 20px; top: 50%;
  transform: translateY(-50%);
  display: flex; align-items: center; gap: 8px; font-size: 0.9rem;
}
.status-indicator {
  width: 12px; height: 12px; border-radius: 50%; background-color: #ff5722;
  box-shadow: 0 0 8px #ff5722; transition: all 0.3s ease;
}
.status-indicator.connected {
  background-color: #00ff7f; box-shadow: 0 0 10px #00ff7f;
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
  position: absolute; top: 65px; right: 20px; pointer-events: none;
}
.controls-group {
  pointer-events: auto; display: grid; gap: 8px;
}
.camera-controls {
  grid-template-columns: 1fr 1fr; width: 280px;
}
.view-controls {
  grid-template-columns: 1fr 1fr 1fr; width: 240px;
}
.control-btn {
  padding: 12px 10px; font-size: 1rem; font-weight: 600;
  color: #fff; background-color: rgba(20, 40, 80, 0.7);
  border: 1px solid rgba(0, 191, 255, 0.6); border-radius: 8px;
  cursor: pointer; transition: all 0.2s ease; backdrop-filter: blur(5px);
  text-align: center;
}
.control-btn:hover {
  background-color: rgba(0, 191, 255, 0.7); border-color: #fff; transform: scale(1.05);
}
.control-btn:active { transform: scale(0.98); }
.control-btn.selected {
  background-color: #00BFFF; border-color: #fff;
  box-shadow: 0 0 12px rgba(0, 191, 255, 0.8); color: #0d203e; transform: scale(1.05);
}
/* --- 详情弹出框 --- */
.details-popup {
  position: absolute; width: 250px; padding: 15px;
  background-color: rgba(10, 40, 90, 0.85); backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 191, 255, 0.6); border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  color: #fff; font-size: 0.9rem; pointer-events: none;
  transition: opacity 0.2s ease; z-index: 100;
}
.details-popup h4 {
  margin: 0 0 10px 0; color: #00BFFF; font-size: 1rem;
  border-bottom: 1px solid rgba(0, 191, 255, 0.3); padding-bottom: 5px;
}
.details-popup p { margin: 0; line-height: 1.5; }
</style>