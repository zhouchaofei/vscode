<template>
  <div class="annotator-container">
    <canvas ref="videoCanvas" class="background-canvas"></canvas>
    <canvas
      ref="annotationCanvas"
      class="annotation-canvas-layer"
      :style="{ cursor: drawingCursor }"
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
        <aside class="annotations-panel" :class="{ collapsed: !isPanelVisible }">
          <div class="panel-content-wrapper">
            <h2 class="panel-title">标注列表</h2>

            <!-- 1. 添加类型选择 -->
            <div class="annotation-input">
              <h3>添加类型</h3>
              <select v-model="selectedType" class="type-selector">
                <option disabled value="">请选择标注类型</option>
                <option v-for="type in annotationTypes" :key="type" :value="type">{{ type }}</option>
              </select>
            </div>

            <div class="annotation-input">
              <h3>添加标注说明</h3>
              <textarea v-model="currentAnnotation.text" placeholder="在此输入标注说明..."></textarea>
              <div class="input-buttons">
                <button @click="saveAnnotation" class="btn btn-primary">保存</button>
                <button @click="cancelAnnotation" class="btn btn-secondary">取消</button>
              </div>
            </div>

            <div class="annotation-list-wrapper">
              <div v-if="annotations.length === 0" class="no-annotations">
                <p>尚未添加任何标注</p>
                <p>点击右侧箭头展开面板以开始</p>
              </div>
              <div v-else class="annotation-list">
                <div v-for="(annotation, index) in annotations" :key="annotation.id" class="annotation-item" :style="{'border-left-color': annotation.color}">
                  <div class="annotation-header">
                    <span class="annotation-id" :style="{color: annotation.color}">标注 #{{ index + 1 }} ({{ annotation.type }})</span>
                  </div>
                  <div class="annotation-details">
                    <p>名称: {{ annotation.text }}</p>
                  </div>
                  <div class="annotation-actions">
                    <button @click="deleteAnnotation(index)" class="btn-delete">删除</button>
                  </div>
                </div>
              </div>
            </div>

            <div class="panel-footer">
              <button @click="saveAllAnnotations" class="btn btn-primary btn-block">保存所有标注 ({{ annotations.length }})</button>
              <div class="stats-display">
                <div class="stat-item"><span>帧率:</span> <span>{{ fps }} FPS</span></div>
                <div class="stat-item"><span>延迟:</span> <span>{{ latency }} ms</span></div>
                <div class="stat-item"><span>数据量:</span> <span>{{ dataSize }}</span></div>
                <div class="stat-item"><span>时长:</span> <span>{{ uptime }}</span></div>
              </div>
            </div>
          </div>
        </aside>

        <button @click="togglePanel" class="panel-toggle-btn" :class="{ 'panel-visible': isPanelVisible }">
          <span class="arrow"></span>
        </button>
      </main>

      <div class="ptz-controls">
        <button @click="sendPtzCommand('zoom_in')" class="ptz-btn">放大</button>
        <button @click="sendPtzCommand('pan_up')" class="ptz-btn">上移</button>
        <button @click="sendPtzCommand('zoom_out')" class="ptz-btn">缩小</button>
        <button @click="sendPtzCommand('pan_left')" class="ptz-btn">左移</button>
        <button @click="sendPtzCommand('pan_down')" class="ptz-btn">下移</button>
        <button @click="sendPtzCommand('pan_right')" class="ptz-btn">右移</button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';

// Canvas references
const videoCanvas = ref(null);
const annotationCanvas = ref(null);

// --- NEW: Annotation Type Management ---
const annotationTypes = ref(['粱盖', '桥墩', '通道', '匝道', '方向']);
const selectedType = ref(''); // Currently selected annotation type

// Color mapping for different types
const typeColors = {
  '粱盖': '#FFA500', // Orange
  '桥墩': '#FFD700', // Yellow
  '通道': '#32CD32', // Green
  '匝道': '#1E90FF', // Blue
  '方向': '#FF4500'  // Red for arrow
};

// --- State Management ---
const isDrawing = ref(false); // Is a drawing action (mousedown) in progress?
const isActiveDrawing = ref(false); // Is there an unsaved annotation on the canvas?
const isPanelVisible = ref(false);

const currentAnnotation = ref({
  rect: { x: 0, y: 0, width: 0, height: 0 },
  arrow: { startX: 0, startY: 0, endX: 0, endY: 0 },
  text: '',
  type: '',
  color: ''
});
const annotations = ref([]);

// Mouse position variables
const startX = ref(0);
const startY = ref(0);

// Canvas contexts
let videoCtx = null;
let annotationCtx = null;

// WebSocket and stats
const socket = ref(null);
const isConnected = ref(false);
const connectionStatus = ref("未连接");
const frameCount = ref(0);
const fps = ref(0);
const latency = ref(0);
const dataSize = ref('0 KB');
const uptime = ref('00:00:00');
const totalDataSize = ref(0);
let connectionStartTime = null;
let fpsInterval = null;
let uptimeInterval = null;
let fpsCounter = 0;

// Computed property to determine if drawing is allowed
const canDraw = computed(() => isPanelVisible.value && selectedType.value !== '');

// Computed property for cursor style
const drawingCursor = computed(() => {
  if (canDraw.value) {
    return 'crosshair';
  }
  return 'default';
});


// --- Panel and Drawing Control ---
const togglePanel = () => {
  if (isPanelVisible.value && isActiveDrawing.value) {
    resetDrawingState();
    drawAnnotations();
  }
  isPanelVisible.value = !isPanelVisible.value;
  if (!isPanelVisible.value) {
      selectedType.value = ''; // Reset type when panel is closed
  }
};

// --- PTZ Control ---
const sendPtzCommand = async (command) => {
  const apiUrl = 'http://your-camera-api.com/ptz_control';
  console.log(`准备发送 PTZ 指令: ${command}`);
  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command, timestamp: new Date().toISOString() })
    });
    if (!response.ok) throw new Error(`HTTP 错误! 状态码: ${response.status}`);
    const result = await response.json();
    console.log('PTZ 指令发送成功, 响应:', result);
    alert(`指令 "${command}" 已成功发送!`);
  } catch (error) {
    console.error('发送 PTZ 指令失败:', error);
    alert(`指令 "${command}" 发送失败: ${error.message}\n请检查API地址或网络连接。`);
  }
};

// --- Canvas Initialization ---
const initCanvas = () => {
  const container = document.querySelector('.annotator-container');
  if (!container) return;
  const { clientWidth: width, clientHeight: height } = container;

  videoCanvas.value.width = width;
  videoCanvas.value.height = height;
  annotationCanvas.value.width = width;
  annotationCanvas.value.height = height;
  
  videoCtx = videoCanvas.value.getContext('2d');
  annotationCtx = annotationCanvas.value.getContext('2d');
  
  drawAnnotations();
};

// --- WebSocket Connection ---
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
      connectionStartTime = Date.now();
      startFPSCounter();
      startUptimeCounter();
    };
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'frame' && message.data) {
          displayFrame(message.data, message.timestamp);
        }
      } catch (error) {
        if (event.data instanceof ArrayBuffer) {
           processImageData(event.data);
        } else {
          console.error('消息解析错误:', error);
        }
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
  stopFPSCounter();
  stopUptimeCounter();
  resetStats();
};

const displayFrame = (base64Data, timestamp) => {
  frameCount.value++;
  fpsCounter++;
  if (timestamp) {
    latency.value = Math.round(Date.now() - (timestamp * 1000));
  }
  totalDataSize.value += base64Data.length;
  dataSize.value = formatBytes(totalDataSize.value);

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

// --- Stats Helpers ---
const startFPSCounter = () => {
  stopFPSCounter();
  fpsInterval = setInterval(() => { fps.value = fpsCounter; fpsCounter = 0; }, 1000);
};
const stopFPSCounter = () => clearInterval(fpsInterval);
const startUptimeCounter = () => {
  stopUptimeCounter();
  uptimeInterval = setInterval(() => {
    if (connectionStartTime) uptime.value = formatUptime(Date.now() - connectionStartTime);
  }, 1000);
};
const stopUptimeCounter = () => clearInterval(uptimeInterval);
const resetStats = () => {
  frameCount.value = 0; fps.value = 0; latency.value = 0;
  totalDataSize.value = 0; dataSize.value = '0 KB'; uptime.value = '00:00:00';
  connectionStartTime = null;
};
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
const formatUptime = (ms) => {
  const s = Math.floor(ms / 1000);
  return `${String(Math.floor(s / 3600)).padStart(2, '0')}:${String(Math.floor((s % 3600) / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
};

// --- Annotation Drawing Logic ---

// Helper function to draw an arrow
function drawArrow(ctx, fromx, fromy, tox, toy, color) {
    const headlen = 15; // length of head in pixels
    const dx = tox - fromx;
    const dy = toy - fromy;
    const angle = Math.atan2(dy, dx);
    
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 3;

    // line
    ctx.beginPath();
    ctx.moveTo(fromx, fromy);
    ctx.lineTo(tox, toy);
    ctx.stroke();

    // arrowhead
    ctx.beginPath();
    ctx.moveTo(tox, toy);
    ctx.lineTo(tox - headlen * Math.cos(angle - Math.PI / 6), toy - headlen * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(tox - headlen * Math.cos(angle + Math.PI / 6), toy - headlen * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fill();
}

// Main function to draw all annotations
const drawAnnotations = () => {
  if (!annotationCtx) return;
  annotationCtx.clearRect(0, 0, annotationCtx.canvas.width, annotationCtx.canvas.height);

  // Draw the current, temporary annotation
  if (isActiveDrawing.value) {
    const anno = currentAnnotation.value;
    if (anno.type === '方向') {
        if (anno.arrow.endX !== 0) { // Only draw if arrow has been moved
            drawArrow(annotationCtx, anno.arrow.startX, anno.arrow.startY, anno.arrow.endX, anno.arrow.endY, anno.color);
        }
    } else {
        if (anno.rect.width > 0) {
            annotationCtx.strokeStyle = anno.color;
            annotationCtx.fillStyle = `${anno.color}33`; // 20% opacity
            annotationCtx.lineWidth = 2;
            annotationCtx.setLineDash([6, 6]);
            annotationCtx.fillRect(anno.rect.x, anno.rect.y, anno.rect.width, anno.rect.height);
            annotationCtx.strokeRect(anno.rect.x, anno.rect.y, anno.rect.width, anno.rect.height);
            annotationCtx.setLineDash([]);
        }
    }
  }
  
  // Draw all saved annotations
  annotations.value.forEach(anno => {
    annotationCtx.font = 'bold 16px Arial';
    annotationCtx.textBaseline = 'middle';

    // Draw shape
    if (anno.type === '方向') {
        drawArrow(annotationCtx, anno.arrow.startX, anno.arrow.startY, anno.arrow.endX, anno.arrow.endY, anno.color);
    } else {
        annotationCtx.strokeStyle = anno.color;
        annotationCtx.lineWidth = 3;
        annotationCtx.fillStyle = `${anno.color}33`; // 20% opacity
        annotationCtx.fillRect(anno.rect.x, anno.rect.y, anno.rect.width, anno.rect.height);
        annotationCtx.strokeRect(anno.rect.x, anno.rect.y, anno.rect.width, anno.rect.height);
    }
    
    // Draw text label if it exists
    if (anno.text) {
        const text = `${anno.type}: ${anno.text}`;
        const textMetrics = annotationCtx.measureText(text);
        const textWidth = textMetrics.width;
        const textHeight = 24;
        const padding = 8;
        
        let textX, textY;
        if (anno.type === '方向') {
            textX = anno.arrow.startX;
            textY = anno.arrow.startY - textHeight;
        } else {
            textX = anno.rect.x;
            textY = anno.rect.y - textHeight;
        }

        // Label background
        annotationCtx.fillStyle = `${anno.color}CC`; // 80% opacity
        annotationCtx.fillRect(textX, textY, textWidth + padding * 2, textHeight);
        
        // Label text
        annotationCtx.fillStyle = 'white';
        annotationCtx.fillText(text, textX + padding, textY + textHeight / 2);
    }
  });
};

// --- Mouse Event Handlers ---
const handleMouseDown = (e) => {
  if (!canDraw.value) return;
  
  if (isActiveDrawing.value) {
    resetDrawingState(); // Clear previous unsaved drawing
  }
  
  isDrawing.value = true;
  isActiveDrawing.value = true;
  const rect = annotationCanvas.value.getBoundingClientRect();
  startX.value = e.clientX - rect.left;
  startY.value = e.clientY - rect.top;

  currentAnnotation.value.type = selectedType.value;
  currentAnnotation.value.color = typeColors[selectedType.value];

  if (selectedType.value === '方向') {
      currentAnnotation.value.arrow = { startX: startX.value, startY: startY.value, endX: 0, endY: 0 };
  } else {
      currentAnnotation.value.rect = { x: startX.value, y: startY.value, width: 0, height: 0 };
  }
  
  annotationCanvas.value.addEventListener('mousemove', handleMouseMove);
  annotationCanvas.value.addEventListener('mouseup', handleMouseUp);
};

const handleMouseMove = (e) => {
  if (!isDrawing.value) return;

  const rect = annotationCanvas.value.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  
  if (currentAnnotation.value.type === '方向') {
      currentAnnotation.value.arrow.endX = mouseX;
      currentAnnotation.value.arrow.endY = mouseY;
  } else {
      currentAnnotation.value.rect = {
        x: Math.min(startX.value, mouseX),
        y: Math.min(startY.value, mouseY),
        width: Math.abs(mouseX - startX.value),
        height: Math.abs(mouseY - startY.value)
      };
  }
  drawAnnotations();
};

const handleMouseUp = (e) => {
    if (!isDrawing.value) return;
    const rect = annotationCanvas.value.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Finalize position for arrow
    if (currentAnnotation.value.type === '方向') {
        currentAnnotation.value.arrow.endX = mouseX;
        currentAnnotation.value.arrow.endY = mouseY;
    }

    isDrawing.value = false;
    annotationCanvas.value.removeEventListener('mousemove', handleMouseMove);
    annotationCanvas.value.removeEventListener('mouseup', handleMouseUp);
    drawAnnotations();
};

// --- Annotation Actions ---
const saveAnnotation = () => {
  const anno = currentAnnotation.value;
  const isRectValid = anno.type !== '方向' && anno.rect.width > 0;
  const isArrowValid = anno.type === '方向' && anno.arrow.endX !== 0;

  if (anno.text.trim() && (isRectValid || isArrowValid)) {
    annotations.value.push({
      ...JSON.parse(JSON.stringify(anno)), // Deep copy
      id: 'anno-' + Date.now().toString(36)
    });
    resetDrawingState();
    drawAnnotations();
  } else {
    alert("请输入标注说明并绘制一个有效的形状 (矩形或箭头)。");
  }
};

const cancelAnnotation = () => {
  resetDrawingState();
  drawAnnotations();
};

const resetDrawingState = () => {
  currentAnnotation.value = {
    rect: { x: 0, y: 0, width: 0, height: 0 },
    arrow: { startX: 0, startY: 0, endX: 0, endY: 0 },
    text: '',
    type: '',
    color: ''
  };
  isActiveDrawing.value = false;
  // Do not reset selectedType here, user might want to draw another of the same type
};

const deleteAnnotation = (index) => {
  annotations.value.splice(index, 1);
  drawAnnotations();
};

const saveAllAnnotations = () => {
  if (annotations.value.length === 0) {
    alert("没有可以保存的标注。");
    return;
  }
  const dataStr = JSON.stringify(annotations.value, null, 2);
  const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
  const exportFileDefaultName = `video-annotations-${new Date().toISOString().slice(0, 10)}.json`;
  
  const linkElement = document.createElement('a');
  linkElement.setAttribute('href', dataUri);
  linkElement.setAttribute('download', exportFileDefaultName);
  linkElement.click();
  
  alert(`已成功保存 ${annotations.value.length} 个标注。`);
};

// --- Lifecycle Hooks ---
onMounted(() => {
  initCanvas();
  connectWebSocket();
  if (annotationCanvas.value) {
    annotationCanvas.value.addEventListener('mousedown', handleMouseDown);
  }
  window.addEventListener('resize', initCanvas);
});

onUnmounted(() => {
  handleDisconnect("组件已卸载");
  window.removeEventListener('resize', initCanvas);
  if (annotationCanvas.value) {
    annotationCanvas.value.removeEventListener('mousedown', handleMouseDown);
  }
});
</script>

<style scoped>
/* Global container and background */
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
.annotation-canvas-layer { z-index: 2; }

/* UI Overlay */
.ui-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 3;
  pointer-events: none;
  display: flex;
  flex-direction: column;
}

/* Header */
.app-header {
  position: relative;
  height: 50px;
  width: 100%;
  color: #fff;
  background: linear-gradient( to right, rgba(0, 123, 255, 0) 0%, rgba(0, 123, 255, 0.6) 20%, rgba(0, 123, 255, 1) 50%, rgba(0, 123, 255, 0.6) 80%, rgba(0, 123, 255, 0) 100% );
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8), 0 0 10px rgba(0, 191, 255, 0.5);
  pointer-events: none;
  flex-shrink: 0;
}
.app-header h1 {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 2.5rem;
  font-weight: 600;
  pointer-events: auto;
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
  pointer-events: auto;
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

/* Main Content Area */
.main-content {
  flex-grow: 1;
  display: flex;
  padding: 20px;
  pointer-events: none;
  overflow: hidden;
}

/* Annotations Panel */
.annotations-panel {
  position: relative;
  width: 290px;
  height: 100%;
  background-color: rgba(10, 40, 90, 0.75);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 191, 255, 0.5);
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
  color: #fff;
  display: flex;
  flex-direction: column;
  pointer-events: auto;
  transition: transform 0.4s ease-in-out;
  transform: translateX(0);
}
.annotations-panel.collapsed {
  transform: translateX(calc(-100% - 20px));
}
.panel-content-wrapper {
  padding: 15px;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Panel Toggle Button */
.panel-toggle-btn {
  position: absolute;
  left: 300px;
  top: 50%;
  transform: translateY(-50%);
  width: 25px;
  height: 60px;
  background-color: rgba(10, 40, 90, 0.85);
  border: 1px solid rgba(0, 191, 255, 0.5);
  border-left: none;
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
  cursor: pointer;
  pointer-events: auto;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: left 0.4s ease-in-out, background-color 0.3s;
}
.panel-toggle-btn.panel-visible { left: 310px; }
.panel-toggle-btn:not(.panel-visible) { left: 0px; }
.panel-toggle-btn .arrow {
  width: 8px;
  height: 8px;
  border-top: 2px solid white;
  border-left: 2px solid white;
  transition: transform 0.4s ease-in-out;
}
.panel-toggle-btn.panel-visible .arrow { transform: rotate(-45deg); }
.panel-toggle-btn:not(.panel-visible) .arrow { transform: rotate(135deg); }
.panel-toggle-btn:hover { background-color: rgba(0, 191, 255, 0.5); }

/* PTZ Controls */
.ptz-controls {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 180px;
  display: grid;
  grid-template-areas:
    "zoom-in pan-up zoom-out"
    "pan-left pan-down pan-right";
  gap: 8px;
  pointer-events: auto;
}
.ptz-btn {
  padding: 10px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  background-color: rgba(20, 40, 80, 0.7);
  border: 1px solid rgba(0, 191, 255, 0.6);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(5px);
}
.ptz-btn:hover {
  background-color: rgba(0, 191, 255, 0.7);
  border-color: #fff;
  transform: scale(1.05);
}
.ptz-btn:active { transform: scale(0.95); }
.ptz-controls button:nth-child(1) { grid-area: zoom-in; }
.ptz-controls button:nth-child(2) { grid-area: pan-up; }
.ptz-controls button:nth-child(3) { grid-area: zoom-out; }
.ptz-controls button:nth-child(4) { grid-area: pan-left; }
.ptz-controls button:nth-child(5) { grid-area: pan-down; }
.ptz-controls button:nth-child(6) { grid-area: pan-right; }

.panel-title {
  font-size: 1.2rem;
  font-weight: 600;
  text-align: center;
  padding: 10px 0;
  margin: -15px -15px 15px -15px;
  background-color: rgba(0, 191, 255, 0.2);
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
  border-bottom: 1px solid rgba(0, 191, 255, 0.5);
  flex-shrink: 0;
}

/* Annotation Input Area */
.annotation-input {
  margin-bottom: 15px;
  flex-shrink: 0;
}
.annotation-input h3 {
  margin-bottom: 10px;
  font-size: 1rem;
  color: #00BFFF;
}
.annotation-input textarea, .type-selector {
  width: 100%;
  background-color: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 191, 255, 0.4);
  border-radius: 5px;
  color: #fff;
  padding: 8px;
  font-family: inherit;
}
.type-selector {
  height: 40px;
}
.type-selector option {
  background-color: #0A285A;
  color: #fff;
}
.annotation-input textarea {
  height: 80px;
  resize: vertical;
}
.annotation-input textarea:focus, .type-selector:focus {
  outline: none;
  border-color: #00BFFF;
  box-shadow: 0 0 8px rgba(0, 191, 255, 0.5);
}
.input-buttons {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

/* Buttons */
.btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 5px;
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  font-size: 0.9rem;
}
.btn-primary {
  background-color: #007bff;
  box-shadow: 0 2px 5px rgba(0, 123, 255, 0.4);
}
.btn-primary:hover {
  background-color: #0069d9;
  transform: translateY(-2px);
}
.btn-secondary {
  background-color: #6c757d;
  box-shadow: 0 2px 5px rgba(108, 117, 125, 0.4);
}
.btn-secondary:hover {
  background-color: #5a6268;
  transform: translateY(-2px);
}
.btn-block {
  width: 100%;
  padding: 12px;
  font-size: 1rem;
}

/* Annotation List */
.annotation-list-wrapper {
  flex-grow: 1;
  overflow: hidden;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 5px;
  padding: 5px;
  display: flex;
}
.annotation-list {
  height: 100%;
  width: 100%;
  overflow-y: auto;
  padding-right: 5px;
}
.annotation-list::-webkit-scrollbar { width: 6px; }
.annotation-list::-webkit-scrollbar-track { background: transparent; }
.annotation-list::-webkit-scrollbar-thumb {
  background-color: rgba(0, 191, 255, 0.5);
  border-radius: 3px;
}
.annotation-list::-webkit-scrollbar-thumb:hover { background-color: rgba(0, 191, 255, 0.8); }

.annotation-item {
  background-color: rgba(0, 191, 255, 0.1);
  border-left: 4px solid; /* Color set dynamically */
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
  transition: background-color 0.3s;
}
.annotation-item:hover { background-color: rgba(0, 191, 255, 0.2); }
.annotation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.annotation-id {
  font-weight: bold;
  /* Color set dynamically */
}
.annotation-details p {
  margin: 4px 0;
  font-size: 0.85rem;
  opacity: 0.9;
}
.annotation-actions {
  text-align: right;
  margin-top: 8px;
}
.btn-delete {
  background-color: transparent;
  border: 1px solid #dc3545;
  color: #dc3545;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}
.btn-delete:hover {
  background-color: #dc3545;
  color: #fff;
}
.no-annotations {
  text-align: center;
  padding: 20px;
  opacity: 0.7;
  margin: auto;
}

/* Panel Footer & Stats */
.panel-footer {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(0, 191, 255, 0.5);
  flex-shrink: 0;
}
.stats-display {
  margin-top: 15px;
  font-size: 0.85rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  opacity: 0.9;
}
.stat-item {
  display: flex;
  justify-content: space-between;
  background-color: rgba(0,0,0,0.2);
  padding: 4px 8px;
  border-radius: 4px;
}
.stat-item span:first-child { color: #00BFFF; }
</style>
