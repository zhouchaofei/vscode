<template>
  <div class="annotator-container">
    <!-- 视频背景层 -->
    <div class="video-background">
      <canvas ref="videoCanvas"></canvas>
      <canvas ref="annotationCanvas"></canvas>
    </div>

    <!-- 控制层 -->
    <div class="control-overlay">
      <div class="connection-status">
        <div class="status-indicator" :class="{ connected: isConnected }"></div>
        <div>{{ connectionStatus }}</div>
      </div>
      
      <div class="annotations-panel">
        <h2 class="section-title">标注列表</h2>
        
        <div class="annotation-input">
          <h3>添加标注说明</h3>
          <textarea v-model="currentAnnotation.text" placeholder="在此输入标注说明..." rows="4"></textarea>
          <div class="input-buttons">
            <button @click="saveAnnotation" class="save-btn">保存</button>
            <button @click="cancelAnnotation" class="cancel-btn">取消</button>
          </div>
        </div>
        
        <div class="scrollable-area" ref="scrollableArea">
          <!-- 标注列表保持不变 -->
        </div>
        
        <button @click="saveAllAnnotations" class="save-all-btn">保存所有标注</button>

        <div class="status-bar">
          <div>标注总数: {{ annotations.length }}</div>
          <div>帧率: {{ fps.toFixed(1) }} FPS</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

// 添加日期和时间显示
const currentDate = ref('')
const currentTime = ref('')
const updateDateTime = () => {
  const now = new Date()
  currentDate.value = now.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit' 
  })
  currentTime.value = now.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 添加时间戳格式化
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

// 初始化日期时间
updateDateTime()
// 每秒更新时间
setInterval(updateDateTime, 1000)

// 变换矩阵状态
const transform = ref({
  scale: 1,
  rotation: 0, // 角度值，单位为度
  offsetX: 0,
  offsetY: 0
})

// 变换控制函数
const rotateLeft = () => {
  transform.value.rotation = (transform.value.rotation - 15) % 360
  drawCanvas()
}

const rotateRight = () => {
  transform.value.rotation = (transform.value.rotation + 15) % 360
  drawCanvas()
}

const zoomIn = () => {
  transform.value.scale = Math.min(transform.value.scale * 1.2, 3)
  drawCanvas()
}

const zoomOut = () => {
  transform.value.scale = Math.max(transform.value.scale / 1.2, 0.5)
  drawCanvas()
}

const resetTransform = () => {
  transform.value = {
    scale: 1,
    rotation: 0,
    offsetX: 0,
    offsetY: 0
  }
  drawCanvas()
}

// 获取当前变换矩阵
const getTransformMatrix = () => {
  const { scale, rotation, offsetX, offsetY } = transform.value
  const rad = rotation * Math.PI / 180
  
  return {
    a: scale * Math.cos(rad),  // 水平缩放
    b: scale * Math.sin(rad),  // 水平倾斜
    c: -scale * Math.sin(rad), // 垂直倾斜
    d: scale * Math.cos(rad),  // 垂直缩放
    e: offsetX,                // 水平移动
    f: offsetY                 // 垂直移动
  }
}

// 屏幕坐标转原始坐标
const screenToOriginal = (x, y) => {
  const matrix = getTransformMatrix()
  // 计算逆矩阵
  const det = matrix.a * matrix.d - matrix.b * matrix.c
  return {
    x: (matrix.d * (x - matrix.e) - matrix.c * (y - matrix.f)) / det,
    y: (-matrix.b * (x - matrix.e) + matrix.a * (y - matrix.f)) / det
  }
}

// 原始坐标转屏幕坐标
const originalToScreen = (x, y) => {
  const matrix = getTransformMatrix()
  return {
    x: matrix.a * x + matrix.c * y + matrix.e,
    y: matrix.b * x + matrix.d * y + matrix.f
  }
}

// 添加滚动区域的引用
const scrollableArea = ref(null)

// 引用Canvas元素
const videoCanvas = ref(null)
const annotationCanvas = ref(null)

// 状态管理
const isDrawing = ref(true)
const isActiveDrawing = ref(false)
const currentAnnotation = ref({
  rect: { x: 0, y: 0, width: 0, height: 0 },
  text: ''
})
const annotations = ref([])
const isConnected = ref(false)
const fps = ref(0)
const frameCount = ref(0)
const startTime = ref(0)
const connectionStatus = ref("连接中...")

// Canvas上下文
let videoCtx = null
let annotationCtx = null
let socket = null

// 初始化Canvas
const initCanvas = () => {
  // 使用窗口尺寸而非容器尺寸
  videoCanvas.value.width = window.innerWidth;
  videoCanvas.value.height = window.innerHeight;
  annotationCanvas.value.width = window.innerWidth;
  annotationCanvas.value.height = window.innerHeight;
  
  videoCtx = videoCanvas.value.getContext('2d')
  annotationCtx = annotationCanvas.value.getContext('2d')
  annotationCtx.lineWidth = 3
  
  drawCanvas()
}

// 建立WebSocket连接
const connectWebSocket = () => {
  socket = new WebSocket('ws://10.1.40.6:3000')
  socket.binaryType = 'arraybuffer'
  
  socket.onopen = () => {
    isConnected.value = true
    connectionStatus.value = "已连接"
    startTime.value = performance.now()
    frameCount.value = 0
  }
  
  socket.onmessage = (event) => {
    if (typeof event.data === 'string') {
      console.log('Received header:', event.data)
    } else {
      frameCount.value++
      
      const elapsed = (performance.now() - startTime.value) / 1000
      if (elapsed >= 1) {
        fps.value = frameCount.value / elapsed
        frameCount.value = 0
        startTime.value = performance.now()
      }
      
      processImageData(event.data)
    }
  }
  
  socket.onclose = () => {
    isConnected.value = false
    connectionStatus.value = "连接已断开"
  }
  
  socket.onerror = (error) => {
    console.error('WebSocket error:', error)
    connectionStatus.value = "连接错误"
  }
}

// 处理图像数据
const processImageData = (data) => {
  const blob = new Blob([data], { type: 'image/jpeg' })
  const url = URL.createObjectURL(blob)
  const img = new Image()
  
  img.onload = () => {
    if (videoCtx) {
      videoCtx.clearRect(0, 0, videoCtx.canvas.width, videoCtx.canvas.height)
      
      // 应用变换到视频
      const matrix = getTransformMatrix()
      videoCtx.save()
      videoCtx.transform(matrix.a, matrix.b, matrix.c, matrix.d, matrix.e, matrix.f)
      videoCtx.drawImage(img, 0, 0, videoCtx.canvas.width, videoCtx.canvas.height)
      videoCtx.restore()
    }
    URL.revokeObjectURL(url)
    drawCanvas()
  }
  
  img.src = url
}

// 鼠标按下事件处理
const handleMouseDown = (e) => {
  if (!isDrawing.value) return
  
  if (isActiveDrawing.value) {
    currentAnnotation.value.rect = { x: 0, y: 0, width: 0, height: 0 }
  }
  
  isActiveDrawing.value = true

  const rect = annotationCanvas.value.getBoundingClientRect()
  const screenX = e.clientX - rect.left
  const screenY = e.clientY - rect.top
  
  // 转换为原始坐标
  const originalPos = screenToOriginal(screenX, screenY)
  
  startX.value = originalPos.x
  startY.value = originalPos.y
  
  annotationCanvas.value.addEventListener('mousemove', handleMouseMove)
  annotationCanvas.value.addEventListener('mouseup', handleMouseUp)
}

// 鼠标移动事件处理
const handleMouseMove = (e) => {
  const rect = annotationCanvas.value.getBoundingClientRect()
  const screenX = e.clientX - rect.left
  const screenY = e.clientY - rect.top
  
  // 转换为原始坐标
  const originalPos = screenToOriginal(screenX, screenY)
  
  currentAnnotation.value.rect = {
    x: Math.min(startX.value, originalPos.x),
    y: Math.min(startY.value, originalPos.y),
    width: Math.abs(originalPos.x - startX.value),
    height: Math.abs(originalPos.y - startY.value)
  }

  drawCanvas()
}

// 鼠标释放事件处理
const handleMouseUp = () => {
  annotationCanvas.value.removeEventListener('mousemove', handleMouseMove)
  annotationCanvas.value.removeEventListener('mouseup', handleMouseUp)
  drawCanvas()
}

// 绘制Canvas
const drawCanvas = () => {
  if (!annotationCtx) return
  
  annotationCtx.clearRect(0, 0, annotationCtx.canvas.width, annotationCtx.canvas.height)
  
  // 保存当前状态
  annotationCtx.save()
  
  // 应用变换
  const matrix = getTransformMatrix()
  annotationCtx.transform(matrix.a, matrix.b, matrix.c, matrix.d, matrix.e, matrix.f)
  
  // 绘制临时矩形
  if (isActiveDrawing.value && currentAnnotation.value.rect.width > 0 && currentAnnotation.value.rect.height > 0) {
    const rect = currentAnnotation.value.rect
    annotationCtx.strokeStyle = '#FF5722'
    annotationCtx.setLineDash([5, 5])
    annotationCtx.strokeRect(rect.x, rect.y, rect.width, rect.height)
    annotationCtx.setLineDash([])
  }
  
  // 绘制已保存的标注
  annotations.value.forEach(anno => {
    const rect = anno.rect
    
    annotationCtx.fillStyle = 'rgba(76, 175, 80, 0.2)'
    annotationCtx.fillRect(rect.x, rect.y, rect.width, rect.height)
    
    annotationCtx.strokeStyle = '#4CAF50'
    annotationCtx.lineWidth = 2
    annotationCtx.strokeRect(rect.x, rect.y, rect.width, rect.height)
    
    annotationCtx.font = 'bold 25px Arial'
    const text = anno.text
    const textWidth = annotationCtx.measureText(text).width
    const textHeight = 30
    const padding = 10
    
    annotationCtx.fillStyle = 'rgba(76, 175, 80, 0.7)'
    annotationCtx.fillRect(
      rect.x,
      rect.y - textHeight,
      textWidth + padding * 2,
      textHeight
    )
    
    annotationCtx.fillStyle = 'white'
    annotationCtx.textBaseline = 'middle'
    annotationCtx.fillText(
      text,
      rect.x + padding,
      rect.y - textHeight / 2
    )
  })
  
  // 恢复状态
  annotationCtx.restore()
}

// 保存标注
const saveAnnotation = () => {
  if (currentAnnotation.value.text.trim() !== '' && 
      currentAnnotation.value.rect.width > 0 && 
      currentAnnotation.value.rect.height > 0) {
    
    const annotationWithId = {
      ...currentAnnotation.value,
      id: 'anno-' + Date.now().toString(36)
    }
    
    annotations.value.push(annotationWithId)
    resetDrawingState()
    drawCanvas()
  }
}

// 取消标注
const cancelAnnotation = () => {
  resetDrawingState()
  drawCanvas()
}

// 重置绘制状态
const resetDrawingState = () => {
  currentAnnotation.value = {
    rect: { x: 0, y: 0, width: 0, height: 0 },
    text: ''
  }
  isActiveDrawing.value = false
}

// 删除标注
const deleteAnnotation = (index) => {
  annotations.value.splice(index, 1)
  drawCanvas()
}

// 保存所有标注
const saveAllAnnotations = () => {
  const dataStr = JSON.stringify(annotations.value, null, 2)
  const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
  
  const exportFileDefaultName = `video-annotations-${new Date().toISOString().slice(0, 10)}.json`
  
  const linkElement = document.createElement('a')
  linkElement.setAttribute('href', dataUri)
  linkElement.setAttribute('download', exportFileDefaultName)
  linkElement.click()
  
  alert(`已保存 ${annotations.value.length} 个标注`)
}

// 鼠标位置变量
const startX = ref(0)
const startY = ref(0)

// 生命周期钩子
onMounted(() => {
  initCanvas()
  connectWebSocket()

  if (annotationCanvas.value) {
    annotationCanvas.value.addEventListener('mousedown', handleMouseDown)
  }
  
  window.addEventListener('resize', initCanvas)

  // 计算滚动区域高度
  const calculateScrollHeight = () => {
    // ... (原有实现)
  }
  
  calculateScrollHeight()
  window.addEventListener('resize', calculateScrollHeight)
  watch(annotations, () => {
    nextTick(calculateScrollHeight)
  })
})

onUnmounted(() => {
  if (socket) {
    socket.close()
  }
  
  window.removeEventListener('resize', initCanvas)
  
  if (annotationCanvas.value) {
    annotationCanvas.value.removeEventListener('mousedown', handleMouseDown)
  }
})
</script>

<style scoped>
.annotator-container {
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #1a2980, #26d0ce);
  padding: 20px;
  box-sizing: border-box;
  font-family: 'Microsoft YaHei', sans-serif;
  color: white;
}

.annotator-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgba(0, 20, 40, 0.7);
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

/* 顶部标题栏样式 */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 25px;
  background: rgba(0, 30, 60, 0.8);
  border-bottom: 1px solid rgba(100, 180, 255, 0.3);
}

.date-time {
  text-align: center;
  background: rgba(0, 60, 120, 0.6);
  padding: 8px 15px;
  border-radius: 8px;
  min-width: 120px;
}

.date {
  font-size: 1.1rem;
  font-weight: bold;
}

.time {
  font-size: 1.4rem;
  font-weight: bold;
  color: #4fc3f7;
}

.title-section {
  text-align: center;
}

.title-section h1 {
  font-size: 1.8rem;
  margin: 0;
  background: linear-gradient(90deg, #4facfe, #00f2fe);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.notification {
  background: rgba(255, 50, 50, 0.8);
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.9rem;
  margin-top: 5px;
  display: inline-block;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.expand-btn, .close-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 5px;
  background: rgba(30, 136, 229, 0.8);
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
}

.expand-btn:hover, .close-btn:hover {
  background: rgba(30, 136, 229, 1);
  transform: translateY(-2px);
}

/* 内容区域 */
.content-container {
  display: flex;
  flex: 1;
  padding: 20px;
  gap: 20px;
  overflow: hidden;
}

.video-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.video-container {
  position: relative;
  width: 100%;
  height: 0;
  padding-top: 56.25%; /* 16:9 Aspect Ratio */
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  background: #000;
}

video, canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 10px;
}

canvas {
  cursor: crosshair;
}

/* 标注区域样式 */
.annotations-section {
  width: 320px;
  display: flex;
  flex-direction: column;
  background: rgba(0, 30, 60, 0.6);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
}

.annotations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: rgba(0, 50, 100, 0.7);
  border-bottom: 1px solid rgba(100, 180, 255, 0.3);
}

.legend {
  background: rgba(30, 136, 229, 0.8);
  padding: 5px 12px;
  border-radius: 15px;
  font-size: 0.9rem;
}

.section-title {
  font-size: 1.3rem;
  margin: 0;
  color: #4fc3f7;
}

.annotations-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 15px;
}

.annotation-input {
  background: rgba(0, 40, 80, 0.5);
  border-radius: 10px;
  padding: 15px;
  margin-bottom: 15px;
}

.annotation-input h3 {
  color: #4fc3f7;
  margin-top: 0;
  margin-bottom: 10px;
}

.annotation-input textarea {
  width: 100%;
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 8px;
  background: rgba(0, 20, 40, 0.7);
  color: white;
  border: 1px solid rgba(100, 180, 255, 0.3);
  resize: vertical;
  font-family: inherit;
}

.annotation-input textarea:focus {
  outline: none;
  border-color: #4fc3f7;
  box-shadow: 0 0 0 2px rgba(79, 195, 247, 0.3);
}

.input-buttons {
  display: flex;
  gap: 10px;
}

.save-btn, .cancel-btn {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 6px;
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
}

.save-btn {
  background: linear-gradient(90deg, #2196F3, #21CBF3);
}

.cancel-btn {
  background: linear-gradient(90deg, #4776E6, #8E54E9);
}

.save-btn:hover, .cancel-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}

/* 标注列表区域 */
.scrollable-area {
  flex: 1;
  overflow-y: auto;
  background: rgba(0, 20, 40, 0.4);
  border-radius: 10px;
  padding: 10px;
}

.annotation-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.annotation-item {
  background: rgba(30, 136, 229, 0.2);
  border-radius: 8px;
  padding: 12px;
  border-left: 3px solid #2196F3;
  transition: all 0.3s;
  backdrop-filter: blur(5px);
}

.annotation-item:hover {
  background: rgba(30, 136, 229, 0.3);
  transform: translateY(-2px);
}

.annotation-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.annotation-id {
  font-weight: bold;
  color: #4fc3f7;
}

.annotation-time {
  font-size: 0.85rem;
  opacity: 0.8;
}

.annotation-position {
  display: flex;
  gap: 15px;
  font-size: 0.9rem;
  opacity: 0.9;
  margin-bottom: 8px;
}

.annotation-content {
  padding: 8px 0;
  border-top: 1px dashed rgba(100, 180, 255, 0.3);
  margin-bottom: 10px;
}

.annotation-actions {
  display: flex;
  justify-content: flex-end;
}

.action-btn {
  padding: 5px 15px;
  border-radius: 5px;
  background: rgba(0, 40, 80, 0.6);
  border: none;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: rgba(0, 60, 120, 0.8);
}

.delete-btn {
  background: rgba(244, 67, 54, 0.3);
}

.delete-btn:hover {
  background: rgba(244, 67, 54, 0.5);
}

/* 底部区域 */
.annotations-footer {
  padding: 15px;
  background: rgba(0, 40, 80, 0.7);
  border-top: 1px solid rgba(100, 180, 255, 0.3);
}

.save-all-btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(90deg, #2196F3, #21CBF3);
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 12px;
}

.save-all-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.status-bar {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  opacity: 0.9;
}

/* 视频背景层 - 全屏 */
.video-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.video-background canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

#annotationCanvas {
  cursor: crosshair;
  z-index: 2;
}

/* 控制层 - 覆盖在视频上方 */
.control-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 3;
  pointer-events: none; /* 允许点击穿透到画布 */
}

/* 连接状态 */
/* .connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 20px;
} */
 .connection-status {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 10px;
  padding: 10px 15px;
  display: flex;
  align-items: center;
  gap: 8px;
  pointer-events: auto; /* 允许交互 */
}

.annotations-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 300px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 15px;
  padding: 15px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  pointer-events: auto; /* 允许交互 */
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #ff5722;
}

.status-indicator.connected {
  background-color: #4CAF50;
}

.no-annotations {
  text-align: center;
  padding: 30px 0;
  opacity: 0.7;
}

/* 滚动条样式 */
.scrollable-area::-webkit-scrollbar {
  width: 8px;
}

.scrollable-area::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

.scrollable-area::-webkit-scrollbar-thumb {
  background: rgba(79, 195, 247, 0.6);
  border-radius: 4px;
}

.scrollable-area::-webkit-scrollbar-thumb:hover {
  background: rgba(79, 195, 247, 0.8);
}

/* 移除原有的视频容器样式 */
.video-container {
  display: none;
}

@media (max-width: 900px) {
  .content-container {
    flex-direction: column;
  }
  
  .annotations-section {
    width: 100%;
    height: 400px;
  }
    .annotations-panel {
    width: calc(100% - 40px);
    bottom: 20px;
    top: auto;
    height: auto;
    max-height: 50vh;
  }
}
</style>