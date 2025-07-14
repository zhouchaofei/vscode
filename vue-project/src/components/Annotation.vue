<template>
  <div class="annotator-container">
    <canvas ref="videoCanvas" class="background-canvas"></canvas>
    
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
          <div class="status-indicator" :class="{ connected: isConnected }"></div>
          <span>{{ connectionStatus }}</span>
        </div>
      </header>

      <main class="main-content">
        <div v-if="hoveredAnnotation" class="details-popup" :style="{ top: popupPosition.y + 'px', left: popupPosition.x + 'px' }">
          <h4>{{ hoveredAnnotation.title }}</h4>
          <p>{{ hoveredAnnotation.details }}</p>
        </div>
      </main>

      <div class="view-controls">
        <button @click="switchView('view_1')" class="view-btn">视角1</button>
        <button @click="switchView('view_2')" class="view-btn">视角2</button>
        <button @click="switchView('view_3')" class="view-btn">视角3</button>
        <button @click="switchView('view_4')" class="view-btn">视角4</button>
        <button @click="switchView('view_5')" class="view-btn">视角5</button>
        <button @click="switchView('view_6')" class="view-btn">视角6</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

// --- Canvas 和状态管理 ---
const videoCanvas = ref(null);
const annotationCanvas = ref(null);
let videoCtx = null;
let annotationCtx = null;

const annotations = ref([]); // 保存来自后端的标注数据
const hoveredAnnotation = ref(null); // 保存当前鼠标悬停的标注
const popupPosition = ref({ x: 0, y: 0 }); // 详情弹出框的位置
const canvasCursor = ref('default'); // 用于在悬停时将光标变为'pointer'

// 不同标注类型的颜色映射
const typeColors = {
  '粱盖': '#FFA500', // 橙色
  '桥墩': '#FFD700', // 黄色
  '通道': '#32CD32', // 绿色
  '匝道': '#1E90FF', // 蓝色
  '方向': '#FF4500'  // 红色
};

// --- WebSocket 和连接状态 ---
const socket = ref(null);
const isConnected = ref(false);
const connectionStatus = ref("未连接");

// --- 组件生命周期钩子 ---
onMounted(() => {
  initCanvas();
  connectWebSocket();
  fetchAnnotations(); // 组件加载时获取标注
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  handleDisconnect("组件已卸载");
  window.removeEventListener('resize', handleResize);
});

// --- Canvas 和绘制 ---
const initCanvas = () => {
  const container = document.querySelector('.annotator-container');
  if (!container) return;
  const { clientWidth: width, clientHeight: height } = container;

  // 设置两个canvas的尺寸相同
  [videoCanvas, annotationCanvas].forEach(canvasRef => {
    if(canvasRef.value) {
      canvasRef.value.width = width;
      canvasRef.value.height = height;
    }
  });
  
  videoCtx = videoCanvas.value.getContext('2d');
  annotationCtx = annotationCanvas.value.getContext('2d');
  
  drawAnnotations(); // 窗口大小调整时重绘标注
};

const handleResize = () => {
    initCanvas();
    fetchAnnotations(); // 可选：如果标注位置是相对于屏幕尺寸的，则重新获取
}

/**
 * 将 `annotations` ref 中存储的所有标注绘制到画布上。
 */
const drawAnnotations = () => {
  if (!annotationCtx) return;
  annotationCtx.clearRect(0, 0, annotationCtx.canvas.width, annotationCtx.canvas.height);

  annotations.value.forEach(anno => {
    const color = typeColors[anno.type] || '#FFFFFF'; // 如果类型未知，默认为白色
    const coordinates = anno.coordinates;
    
    if (!coordinates || coordinates.length < 2) return;

    annotationCtx.lineWidth = 3;
    annotationCtx.strokeStyle = color;
    annotationCtx.fillStyle = `${color}4D`; // 30% 透明度填充

    // 绘制多边形
    annotationCtx.beginPath();
    annotationCtx.moveTo(coordinates[0].x, coordinates[0].y);
    for (let i = 1; i < coordinates.length; i++) {
      annotationCtx.lineTo(coordinates[i].x, coordinates[i].y);
    }
    annotationCtx.closePath();
    annotationCtx.stroke();
    annotationCtx.fill();

    // 在图形上绘制标题文本
    annotationCtx.fillStyle = '#FFFFFF';
    annotationCtx.font = 'bold 16px Arial';
    annotationCtx.textBaseline = 'top';
    const textX = coordinates[0].x + 10;
    const textY = coordinates[0].y + 10;
    annotationCtx.fillText(anno.title, textX, textY);
  });
};


// --- 后端数据与交互 ---

/**
 * 建议的后端响应JSON结构：
 * [
 * {
 * "id": "anno_001",
 * "type": "桥墩",
 * "title": "主桥墩 #A1",
 * "details": "承重结构，建于2022年，混凝土强度C50。",
 * "coordinates": [
 * { "x": 150, "y": 400 },
 * { "x": 250, "y": 420 },
 * { "x": 260, "y": 600 },
 * { "x": 160, "y": 580 }
 * ]
 * },
 * {
 * "id": "anno_002",
 * "type": "粱盖",
 * "title": "粱盖 #B2",
 * "details": "钢结构，2023年进行过安全检查。",
 * "coordinates": [
 * { "x": 100, "y": 350 },
 * { "x": 800, "y": 370 },
 * { "x": 790, "y": 410 },
 * { "x": 90, "y": 390 }
 * ]
 * }
 * ]
 */
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
      {
        id: "anno_001",
        type: "桥墩",
        title: "1#桥墩",
        details: "承重结构，建于2022年，混凝土强度C50。",
        coordinates: [ { "x": 179.6327, "y": 786.27796 }, { "x": 180.133555, "y": 827.34641 }, { "x": 226.5442404, "y": 828.0141903 }, { "x": 228.213689, "y": 785.7771285 } ]
      },
      {
        id: "anno_002",
        type: "粱盖",
        title: "粱盖 #B2",
        details: "钢结构，2023年进行过安全检查。",
        coordinates: [ { "x": 100, "y": 350 }, { "x": 800, "y": 370 }, { "x": 790, "y": 410 }, { "x": 90, "y": 390 } ]
      },
       {
        id: "anno_003",
        type: "匝道",
        title: "入口匝道",
        details: "通往市中心方向，限速60km/h。",
        coordinates: [ { "x": 900, "y": 500 }, { "x": 1200, "y": 550 }, { "x": 1180, "y": 600 }, { "x": 880, "y": 540 } ]
      }
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
 * 通过向后端发送命令来切换视图。
 * 这通常会触发视频流的更改和一套新的标注。
 * @param {string} viewId - 要切换到的视图ID (例如 'view_1')。
 */
const switchView = async (viewId) => {
  console.log(`准备切换到视角: ${viewId}`);
  try {
    const response = await fetch('/api/switch_view', { // 虚拟的API端点
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ view: viewId, timestamp: new Date().toISOString() })
    });
    if (!response.ok) throw new Error(`HTTP 错误! 状态码: ${response.status}`);
    const result = await response.json();
    console.log('视角切换成功, 响应:', result);
    alert(`已发送指令切换到 "${viewId}"!`);

    // 成功切换视图后，获取新的标注
    await fetchAnnotations();

  } catch (error) {
    console.error(`切换到 ${viewId} 失败:`, error);
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
  const mousePos = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  };

  // 查找鼠标悬停在哪个标注上（反向检查以优先处理顶层）
  const currentHover = annotations.value.slice().reverse().find(anno => 
    isPointInPolygon(mousePos, anno.coordinates)
  );

  if (currentHover) {
    hoveredAnnotation.value = currentHover;
    // 将弹出框定位在光标右侧，并进行边界检查
    popupPosition.value.x = Math.min(mousePos.x + 15, rect.width - 220); // 220 是弹出框的大约宽度
    popupPosition.value.y = Math.min(mousePos.y + 15, rect.height - 100); // 100 是弹出框的大约高度
    canvasCursor.value = 'pointer';
  } else {
    hoveredAnnotation.value = null;
    canvasCursor.value = 'default';
  }
};

// --- WebSocket 连接逻辑 (基本未变) ---
const connectWebSocket = () => {
  if (isConnected.value) return;
  const serverUrl = 'ws://59.110.65.210:8765';
  connectionStatus.value = "连接中...";
  try {
    const ws = new WebSocket(serverUrl);
    socket.value = ws;
    ws.onopen = () => {
      isConnected.value = true;
      connectionStatus.value = "已连接";
    };
    ws.onmessage = (event) => {
      // 处理传入视频帧的逻辑
      if (typeof event.data === 'string') {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'frame' && message.data) {
            displayFrame(message.data);
          }
        } catch(e) { /* 不是JSON消息，可能是其他数据类型 */ }
      } else if (event.data instanceof Blob || event.data instanceof ArrayBuffer) {
        processImageData(event.data);
      }
    };
    ws.onclose = () => handleDisconnect('连接已断开');
    ws.onerror = () => handleDisconnect('连接错误');
  } catch (error) {
    handleDisconnect('连接失败');
  }
};

const handleDisconnect = (statusText) => {
  isConnected.value = false;
  connectionStatus.value = statusText;
  if (socket.value) {
    socket.value.close();
    socket.value = null;
  }
};

const displayFrame = (base64Data) => {
  const img = new Image();
  img.onload = () => {
    if (videoCtx) {
      videoCtx.clearRect(0, 0, videoCtx.canvas.width, videoCtx.canvas.height);
      videoCtx.drawImage(img, 0, 0, videoCtx.canvas.width, videoCtx.canvas.height);
    }
  };
  img.src = 'data:image/jpeg;base64,' + base64Data;
};

const processImageData = (data) => {
  const blob = new Blob([data], { type: 'image/jpeg' });
  const url = URL.createObjectURL(blob);
  const img = new Image();
  img.onload = () => {
    if (videoCtx) {
      videoCtx.clearRect(0, 0, videoCtx.canvas.width, videoCtx.canvas.height);
      videoCtx.drawImage(img, 0, 0, videoCtx.canvas.width, videoCtx.canvas.height);
    }
    URL.revokeObjectURL(url);
  };
  img.src = url;
};

</script>

<style scoped>
/* --- 基础布局 --- */
.annotator-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  background-color: #000;
  overflow: hidden;
  font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.background-canvas, .annotation-canvas-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
.background-canvas { z-index: 1; }
.annotation-canvas-layer { z-index: 3; /* 在视频之上，UI之下 */ }

/* --- UI 覆盖层 --- */
.ui-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 4;
  pointer-events: none; /* 允许点击穿透到canvas */
  display: flex;
  flex-direction: column;
}

.main-content {
  flex-grow: 1;
  position: relative;
}

/* --- 头部 --- */
.app-header {
  position: relative;
  height: 50px;
  width: 100%;
  color: #fff;
  background: linear-gradient( to right, rgba(0, 123, 255, 0) 0%, rgba(0, 123, 255, 0.6) 20%, rgba(0, 123, 255, 1) 50%, rgba(0, 123, 255, 0.6) 80%, rgba(0, 123, 255, 0) 100% );
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

/* --- 详情弹出框 (新) --- */
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
  pointer-events: none; /* 弹出框本身不捕获鼠标事件 */
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

/* --- 视角控件 (替换PTZ) --- */
.view-controls {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 240px; /* 调整宽度 */
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
  pointer-events: auto; /* 按钮可点击 */
}
.view-btn {
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
.view-btn:hover {
  background-color: rgba(0, 191, 255, 0.7);
  border-color: #fff;
  transform: scale(1.05);
}
.view-btn:active {
  transform: scale(0.98);
}
</style>