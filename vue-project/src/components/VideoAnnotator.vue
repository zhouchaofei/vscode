<template>
  <div class="annotator-container">
    <canvas ref="videoCanvas" class="background-canvas"></canvas>
    <canvas ref="annotationCanvas" class="annotation-canvas-layer"></canvas>

    <div class="ui-overlay">
      <header class="app-header">
        <h1>智慧监管平台</h1>
        <div class="connection-status">
          <div class="status-indicator" :class="{ connected: isConnected }"></div>
          <span>{{ connectionStatus }}</span>
        </div>
      </header>

      <main class="main-content">
        <aside class="annotations-panel">
          <h2 class="panel-title">标注列表</h2>
          
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
              <p>在视频上绘制矩形框并添加说明</p>
            </div>
            <div v-else class="annotation-list">
              <div v-for="(annotation, index) in annotations" :key="annotation.id" class="annotation-item">
                <div class="annotation-header">
                  <span class="annotation-id">标注 #{{ index + 1 }}</span>
                </div>
                <div class="annotation-details">
                  <p>名称: {{ annotation.text }}</p>
                  <p>位置: ({{ annotation.rect.x.toFixed(0) }}, {{ annotation.rect.y.toFixed(0) }})</p>
                  <p>尺寸: {{ annotation.rect.width.toFixed(0) }}×{{ annotation.rect.height.toFixed(0) }}</p>
                </div>
                <div class="annotation-actions">
                  <button @click="deleteAnnotation(index)" class="btn-delete">删除</button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="panel-footer">
            <button @click="saveAllAnnotations" class="btn btn-primary btn-block">保存所有标注 ({{ annotations.length }})</button>
            <!-- <div class="fps-display">帧率: {{ fps.toFixed(1) }} FPS</div> -->
            <div class="stats-display">
              <div class="stat-item"><span>帧率:</span> <span>{{ fps }} FPS</span></div>
              <div class="stat-item"><span>延迟:</span> <span>{{ latency }} ms</span></div>
              <div class="stat-item"><span>数据量:</span> <span>{{ dataSize }}</span></div>
              <div class="stat-item"><span>时长:</span> <span>{{ uptime }}</span></div>
            </div>
          </div>
        </aside>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

// Canvas 引用
const videoCanvas = ref(null);
const annotationCanvas = ref(null);

// 状态管理
const isDrawing = ref(true); // 默认开启标注模式
const isActiveDrawing = ref(false); // 是否有活跃的未保存标注
const currentAnnotation = ref({
  rect: { x: 0, y: 0, width: 0, height: 0 },
  text: ''
});
const annotations = ref([]);
// 鼠标位置变量
const startX = ref(0);
const startY = ref(0);

// Canvas 上下文
let videoCtx = null;
let annotationCtx = null;

const socket = ref(null);
const isConnected = ref(false);
const connectionStatus = ref("未连接");

// 详细统计信息
const frameCount = ref(0);
const fps = ref(0);
const latency = ref(0);
const dataSize = ref('0 KB');
const uptime = ref('00:00:00');
const totalDataSize = ref(0);

// 计时器引用
let connectionStartTime = null;
let fpsInterval = null;
let uptimeInterval = null;
let fpsCounter = 0; // 用于在1秒内计数的临时变量

// 初始化 Canvas
const initCanvas = () => {
  const container = document.querySelector('.annotator-container');
  if (!container) return;

  const width = container.clientWidth;
  const height = container.clientHeight;

  // 设置两个 Canvas 的尺寸以填满屏幕
  videoCanvas.value.width = width;
  videoCanvas.value.height = height;
  annotationCanvas.value.width = width;
  annotationCanvas.value.height = height;
  
  // 获取上下文
  videoCtx = videoCanvas.value.getContext('2d');
  annotationCtx = annotationCanvas.value.getContext('2d');
  
  // 初始重绘一次已有的标注
  drawAnnotations();
};

// 建立 WebSocket 连接
const connectWebSocket = () => {
  if (isConnected.value) return;

  // const serverUrl = 'ws://172.16.145.1:8765'; 
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
      console.log('WebSocket连接成功');
    };

    ws.onmessage = (event) => {
      // 假设服务器发送的是JSON字符串
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'frame' && message.data) {
          displayFrame(message.data, message.timestamp);
        }
      } catch (error) {
        // 如果解析失败，可能是 ArrayBuffer，做兼容处理
        // 注意：这是一个降级方案，理想情况下服务器格式应统一
        if (event.data instanceof ArrayBuffer) {
           processImageData(event.data); // 调用旧的处理函数
        } else {
          console.error('消息解析错误:', error);
        }
      }
    };

    ws.onclose = () => {
      handleDisconnect('连接已断开');
      console.log('WebSocket连接关闭');
    };

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
      handleDisconnect('连接错误');
    };

  } catch (error) {
    console.error('连接初始化错误:', error);
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
  // 1. 更新统计数据
  frameCount.value++;
  fpsCounter++;
  
  if (timestamp) {
    latency.value = Math.round(Date.now() - (timestamp * 1000));
  }
  
  // 假设base64字符串的长度约等于字节数 (实际会稍大)
  totalDataSize.value += base64Data.length;
  dataSize.value = formatBytes(totalDataSize.value);

  // 2. 将Base64数据绘制到Canvas
  const img = new Image();
  img.onload = () => {
    if (videoCtx) {
      videoCtx.clearRect(0, 0, videoCtx.canvas.width, videoCtx.canvas.height);
      videoCtx.drawImage(img, 0, 0, videoCtx.canvas.width, videoCtx.canvas.height);
    }
  };
  img.src = 'data:image/jpeg;base64,' + base64Data;
};

// 处理图像数据并绘制到背景 Canvas
// 兼容旧的 ArrayBuffer 格式
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


// --- 新增：从 client.html 移植的辅助函数 ---

const startFPSCounter = () => {
  stopFPSCounter(); // 先停止以防万一
  fpsInterval = setInterval(() => {
    fps.value = fpsCounter;
    fpsCounter = 0;
  }, 1000);
};

const stopFPSCounter = () => {
  if (fpsInterval) {
    clearInterval(fpsInterval);
    fpsInterval = null;
  }
};

const startUptimeCounter = () => {
  stopUptimeCounter();
  uptimeInterval = setInterval(() => {
    if (connectionStartTime) {
      const duration = Date.now() - connectionStartTime;
      uptime.value = formatUptime(duration);
    }
  }, 1000);
};

const stopUptimeCounter = () => {
  if (uptimeInterval) {
    clearInterval(uptimeInterval);
    uptimeInterval = null;
  }
};

const resetStats = () => {
  frameCount.value = 0;
  fps.value = 0;
  latency.value = 0;
  totalDataSize.value = 0;
  dataSize.value = '0 KB';
  uptime.value = '00:00:00';
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
  const seconds = Math.floor(ms / 1000) % 60;
  const minutes = Math.floor(ms / (1000 * 60)) % 60;
  const hours = Math.floor(ms / (1000 * 60 * 60));
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};




// 绘制所有标注
const drawAnnotations = () => {
  if (!annotationCtx) return;
  
  // 清除画布
  annotationCtx.clearRect(0, 0, annotationCtx.canvas.width, annotationCtx.canvas.height);

  // 绘制临时矩形 (用户正在绘制或已绘制但未保存的)
  if (isActiveDrawing.value && currentAnnotation.value.rect.width > 0) {
    annotationCtx.strokeStyle = '#FF5722'; // 橙色虚线框，使其醒目
    annotationCtx.setLineDash([6, 6]);
    annotationCtx.lineWidth = 2;
    annotationCtx.strokeRect(
      currentAnnotation.value.rect.x,
      currentAnnotation.value.rect.y,
      currentAnnotation.value.rect.width,
      currentAnnotation.value.rect.height
    );
    annotationCtx.setLineDash([]);
  }
  
  // 绘制已保存的标注
  annotations.value.forEach(anno => {
    // 边框和填充
    annotationCtx.strokeStyle = '#00BFFF'; // 深天蓝色边框
    annotationCtx.lineWidth = 3;
    annotationCtx.fillStyle = 'rgba(0, 191, 255, 0.2)'; // 20% 透明度的天蓝色填充

    annotationCtx.fillRect(anno.rect.x, anno.rect.y, anno.rect.width, anno.rect.height);
    annotationCtx.strokeRect(anno.rect.x, anno.rect.y, anno.rect.width, anno.rect.height);
    
    // 绘制文本标签
    annotationCtx.font = 'bold 16px Arial';
    const text = anno.text;
    const textMetrics = annotationCtx.measureText(text);
    const textWidth = textMetrics.width;
    const textHeight = 24;
    const padding = 8;

    // 绘制标签背景
    annotationCtx.fillStyle = 'rgba(15, 53, 120, 0.8)'; 
    annotationCtx.fillRect(
      anno.rect.x,
      anno.rect.y - textHeight,
      textWidth + padding * 2,
      textHeight
    );
    
    // 绘制标签文字
    annotationCtx.fillStyle = 'white';
    annotationCtx.textBaseline = 'middle';
    annotationCtx.fillText(
      text,
      anno.rect.x + padding,
      anno.rect.y - textHeight / 2
    );
  });
};

// 鼠标按下事件处理
const handleMouseDown = (e) => {
  if (!isDrawing.value) return;
  
  // 开始新绘制时清除前一个未保存的标注
  if (isActiveDrawing.value) {
    currentAnnotation.value.rect = { x: 0, y: 0, width: 0, height: 0 };
  }
  
  isActiveDrawing.value = true;
  const rect = annotationCanvas.value.getBoundingClientRect();
  startX.value = e.clientX - rect.left;
  startY.value = e.clientY - rect.top;
  
  // 开始绘制
  annotationCanvas.value.addEventListener('mousemove', handleMouseMove);
  annotationCanvas.value.addEventListener('mouseup', handleMouseUp);
};

// 鼠标移动事件处理
const handleMouseMove = (e) => {
  const rect = annotationCanvas.value.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  
  // 计算矩形尺寸
  currentAnnotation.value.rect = {
    x: Math.min(startX.value, mouseX),
    y: Math.min(startY.value, mouseY),
    width: Math.abs(mouseX - startX.value),
    height: Math.abs(mouseY - startY.value)
  };

  // 绘制临时矩形
  drawAnnotations();
};

// 鼠标释放事件处理
const handleMouseUp = () => {
  // 移除事件监听
  annotationCanvas.value.removeEventListener('mousemove', handleMouseMove);
  annotationCanvas.value.removeEventListener('mouseup', handleMouseUp);
  // 保持临时矩形显示直到保存或取消
  drawAnnotations();
};

// 标注操作
const saveAnnotation = () => {
  if (currentAnnotation.value.text.trim() && currentAnnotation.value.rect.width > 0) {
    annotations.value.push({
      ...currentAnnotation.value,
      id: 'anno-' + Date.now().toString(36)
    });
    resetDrawingState();
    drawAnnotations();
  } else {
    alert("请输入标注说明并绘制一个矩形框。");
  }
};

// 取消标注
const cancelAnnotation = () => {
  resetDrawingState();
  drawAnnotations();
};

// 重置绘制状态
const resetDrawingState = () => {
  currentAnnotation.value = {
    rect: { x: 0, y: 0, width: 0, height: 0 },
    text: ''
  };
  isActiveDrawing.value = false;
};

// 删除标注
const deleteAnnotation = (index) => {
  annotations.value.splice(index, 1);
  drawAnnotations();
};

// 保存所有标注
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

// 生命周期钩子
onMounted(() => {
  initCanvas();
  // connectWebSocket();
  connectWebSocket(); // 使用新的连接函数

  // 添加事件监听
  if (annotationCanvas.value) {
    annotationCanvas.value.addEventListener('mousedown', handleMouseDown);
  }
  
  // 窗口大小改变时重新初始化Canvas
  window.addEventListener('resize', initCanvas);
});

onUnmounted(() => {
  // 关闭WebSocket连接
  // if (socket) {
  //   socket.close();
  // }
  handleDisconnect("组件已卸载"); // 使用新的断开连接函数
  
  // 移除事件监听
  window.removeEventListener('resize', initCanvas);
  
  if (annotationCanvas.value) {
    // eslint-disable-next-line
    annotationCanvas.value.removeEventListener('mousedown', handleMouseDown);
  }
});
</script>

<style scoped>
/* 全局容器和背景设置 */
.annotator-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  background-color: #000;
  overflow: hidden;
  font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.background-canvas {
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
  z-index: 2;
  cursor: crosshair;
}

/* UI 浮层 */
.ui-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 3;
  pointer-events: none; /* 允许鼠标事件穿透到下面的 Canvas */
  display: flex;
  flex-direction: column;
}

/* 顶部标题栏 */
.app-header {
position: relative; /* 子元素绝对定位所必需 */
  height: 50px;
  width: 100%;
  color: #fff;
  /* 添加渐变背景 */
  background: linear-gradient(
    to right, 
    rgba(0, 123, 255, 0) 0%, 
    rgba(0, 123, 255, 0.6) 20%,
    rgba(0, 123, 255, 1) 50%,
    rgba(0, 123, 255, 0.6) 80%,
    rgba(0, 123, 255, 0) 100%
  );
  /* 添加底部边框 */
  /* border-bottom: 1px solid rgba(0, 191, 255, 0.3); */
  /* 增强文字阴影 */
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8), 0 0 10px rgba(0, 191, 255, 0.5);
  /* text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5); */
  pointer-events: none; /* 允许点击事件穿透空的头部区域 */
  flex-shrink: 0; /* 防止flex布局压缩标题栏 */
}

.app-header h1 {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%); /* 完美居中元素 */
  font-size: 2.5rem;
  font-weight: 600;
  pointer-events: auto; /* 使文本本身可交互 */
}

.connection-status {
  position: absolute;
  right: 20px; /* 距离右边缘的间距 */
  top: 50%;
  transform: translateY(-50%); /* 使其垂直居中 */
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  pointer-events: auto; /* 确保状态部分可交互 */
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #ff5722; /* 断开连接时为橙色 */
  box-shadow: 0 0 8px #ff5722;
  transition: all 0.3s ease;
}

.status-indicator.connected {
  background-color: #00ff7f; /* 连接时为亮绿色 */
  box-shadow: 0 0 10px #00ff7f;
}

/* 主要内容区域 */
.main-content {
  flex-grow: 1;
  display: flex;
  padding: 20px;
  pointer-events: none; /* 允许鼠标事件穿透 */
  overflow: hidden; /* 防止内容溢出 */
}

/* 左侧标注面板 */
.annotations-panel {
  width: 250px;
  max-height: 100%; /* 确保面板不会超出父容器 */
  background-color: rgba(10, 40, 90, 0.75);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 191, 255, 0.5);
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
  color: #fff;
  display: flex;
  flex-direction: column;
  padding: 15px;
  pointer-events: auto; /* 面板本身可交互 */
  transition: background-color 0.3s;
}

.annotations-panel:hover {
    background-color: rgba(10, 40, 90, 0.85);
}

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

.annotations-panel {
  width: 280px; /* 可以适当加宽以容纳更多信息 */
}

.panel-footer {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(0, 191, 255, 0.5);
  flex-shrink: 0;
}

/* 新增的统计信息样式 */
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
.stat-item span:first-child {
  color: #00BFFF;
}

/* 标注输入区域 */
.annotation-input {
  margin-bottom: 15px;
  flex-shrink: 0;
}

.annotation-input h3 {
  margin-bottom: 10px;
  font-size: 1rem;
  color: #00BFFF;
}

.annotation-input textarea {
  width: 100%;
  height: 80px;
  background-color: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 191, 255, 0.4);
  border-radius: 5px;
  color: #fff;
  padding: 8px;
  resize: vertical;
  font-family: inherit;
}

.annotation-input textarea:focus {
  outline: none;
  border-color: #00BFFF;
  box-shadow: 0 0 8px rgba(0, 191, 255, 0.5);
}

.input-buttons {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

/* 按钮通用样式 */
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


/* 标注列表 */
.annotation-list-wrapper {
  flex-grow: 1; /* 关键：让此容器填充剩余空间 */
  overflow: hidden; /* 关键：配合内部的滚动 */
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 5px;
  padding: 5px;
  display: flex; /* 使用flex布局来处理空状态 */
}

.annotation-list {
  height: 100%;
  width: 100%;
  overflow-y: auto;
  padding-right: 5px;
}

/* 自定义滚动条 */
.annotation-list::-webkit-scrollbar {
  width: 6px;
}
.annotation-list::-webkit-scrollbar-track {
  background: transparent;
}
.annotation-list::-webkit-scrollbar-thumb {
  background-color: rgba(0, 191, 255, 0.5);
  border-radius: 3px;
}
.annotation-list::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 191, 255, 0.8);
}

.annotation-item {
  background-color: rgba(0, 191, 255, 0.1);
  border-left: 4px solid #00BFFF;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
  transition: background-color 0.3s;
}
.annotation-item:hover {
  background-color: rgba(0, 191, 255, 0.2);
}

.annotation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.annotation-id {
  font-weight: bold;
  color: #00BFFF;
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
  margin: auto; /* 在flex容器中居中 */
}

/* 面板底部 */
.panel-footer {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(0, 191, 255, 0.5);
  flex-shrink: 0;
}

.fps-display {
  text-align: center;
  margin-top: 10px;
  font-size: 0.9rem;
  opacity: 0.8;
}

</style>