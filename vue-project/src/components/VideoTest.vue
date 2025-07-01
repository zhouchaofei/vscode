<template>
  <div class="annotator-container">
    <div class="app-container">
      <div class="video-section">
        <h2 class="section-title">视频标注区域</h2>
        <div class="transform-controls">
          <button @click="rotateLeft" class="transform-btn">↺ 左转</button>
          <button @click="rotateRight" class="transform-btn">↻ 右转</button>
          <button @click="zoomIn" class="transform-btn">+ 放大</button>
          <button @click="zoomOut" class="transform-btn">- 缩小</button>
          <button @click="resetTransform" class="transform-btn">重置</button>
        </div>
      </div>

      <div class="connection-status">
        <div class="status-indicator" :class="{ connected: isConnected }"></div>
        <div>{{ connectionStatus }}</div>
      </div>
        
      <div class="video-container">
        <canvas ref="videoCanvas"></canvas>
        <canvas ref="annotationCanvas"></canvas>
      </div>      
      

      <div class="annotations-section">
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
          <div class="annotation-list">
            <div v-if="annotations.length === 0" class="no-annotations">
              <p>尚未添加任何标注</p>
              <p>在视频上绘制矩形框并添加说明</p>
            </div>
            
            <div v-for="(annotation, index) in annotations" :key="annotation.id" class="annotation-item">
              <div class="annotation-header">
                <div class="annotation-id">标注 #{{ index + 1 }}</div>
              </div>
              <div class="annotation-position">
                <div>位置: ({{ annotation.rect.x.toFixed(0) }}, {{ annotation.rect.y.toFixed(0) }})</div>
                <div>尺寸: {{ annotation.rect.width.toFixed(0) }}×{{ annotation.rect.height.toFixed(0) }}</div>
              </div>
              <div class="annotation-content">
                名称: {{ annotation.text }}
              </div>
              <div class="annotation-actions">
                <button @click="deleteAnnotation(index)" class="action-btn delete-btn">删除</button>
              </div>
            </div>
          </div>
        </div>
        
        <button @click="saveAllAnnotations" class="save-all-btn">保存所有标注</button>

        <div class="status-bar">
          <div>标注总数: {{ annotations.length }}</div>
          <div>帧率: {{ fps.toFixed(1) }} FPS</div>
          <div>旋转: {{ transform.rotation }}°</div>
          <div>缩放: {{ (transform.scale * 100).toFixed(0) }}%</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

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
  const container = document.querySelector('.video-container')
  videoCanvas.value.width = container.clientWidth
  videoCanvas.value.height = container.clientHeight
  annotationCanvas.value.width = container.clientWidth
  annotationCanvas.value.height = container.clientHeight
  
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
  height: 100%;
}

.app-container {
  display: grid;
  grid-template-columns: 1fr 200px;
  gap: 10px;
}

.video-section {
  background: rgba(0, 0, 0, 0.4);
  border-radius: 15px;
  padding: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
}

.transform-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 10px 0;
}

.transform-btn {
  padding: 6px 10px;
  border: none;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
  flex: 1;
  min-width: 70px;
}

.transform-btn:hover {
  background: rgba(255, 138, 0, 0.6);
  transform: translateY(-2px);
}

.video-container {
  position: relative;
  width: 100%;
  height: 0;
  padding-top: 56.25%; /* 16:9 Aspect Ratio */
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.7);
  background: #000;
  margin-bottom: 10px;
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

#annotationCanvas {
  cursor: crosshair;
}

.annotations-section {
  background: rgba(0, 0, 0, 0.4);
  border-radius: 15px;
  padding: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.section-title {
  font-size: 1.5rem;
  margin-bottom: 10px;
  border-bottom: 2px solid rgba(255, 255, 255, 0.2);
  text-align: center;
  background: linear-gradient(90deg, #ff8a00, #e52e71);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.annotation-input {
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 15px;
}

.annotation-input h3 {
  color: #ff8a00;
}

.annotation-input textarea {
  width: 100%;
  padding: 10px;
  margin: 10px 0;
  border-radius: 8px;
  background: rgba(255,255,255,0.1);
  color: white;
  border: none;
  resize: vertical;
  font-family: inherit;
}

.annotation-input textarea:focus {
  outline: 1px solid #ff8a00;
}

.input-buttons {
  display: flex;
  gap: 10px;
}

.save-btn {
  padding: 10px 10px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(90deg, #ff8a00, #e52e71);
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  width: 100%;
  font-size: 1rem;
}

.cancel-btn {
  padding: 10px 10px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(90deg, #4776E6, #8E54E9);
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  width: 100%;
  font-size: 1rem;
}

.save-btn:hover, .cancel-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.save-all-btn {
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(90deg, #ff8a00, #e52e71);
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  width: 100%;
  font-size: 1.1rem;
}

.save-all-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.scrollable-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 100%;
}

.annotation-list {
  overflow-y: auto;
  flex: 1;
}

.annotation-list::-webkit-scrollbar {
  width: 8px;
}

.annotation-list::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.annotation-list::-webkit-scrollbar-thumb {
  background: rgba(255, 138, 0, 0.6);
  border-radius: 4px;
}

.annotation-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 138, 0, 0.8);
}

.annotation-item {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 10px;
  border-left: 4px solid #ff8a00;
  transition: all 0.3s;
}

.annotation-item:hover {
  background: rgba(255, 255, 255, 0.15);
}

.annotation-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.annotation-id {
  font-weight: bold;
  color: #ff8a00;
}

.annotation-position {
  font-size: 0.9rem;
  opacity: 0.8;
  margin-bottom: 8px;
}

.annotation-content {
  line-height: 1.5;
  padding: 8px 0;
  border-top: 1px dashed rgba(255, 255, 255, 0.1);
}

.annotation-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

.action-btn {
  padding: 5px 10px;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.delete-btn {
  background: rgba(255, 0, 0, 0.3);
}

.delete-btn:hover {
  background: rgba(255, 0, 0, 0.5);
}

.status-bar {
  display: flex;
  justify-content: space-between;
  padding: 10px 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  font-size: 0.9rem;
  margin-top: auto;
  flex-wrap: wrap;
}

.status-bar > div {
  margin: 3px 5px;
}

.no-annotations {
  text-align: center;
  padding: 30px 0;
  opacity: 0.7;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
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

@media (max-width: 900px) {
  .app-container {
    grid-template-columns: 1fr;
    height: auto;
  }
  
  .annotations-section {
    height: 500px;
  }
}
</style>