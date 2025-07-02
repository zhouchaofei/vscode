<template>
  <div class="annotator-container">
    <!-- 视频背景层 -->
    <div class="video-background">
      <canvas ref="videoCanvas"></canvas>
    </div>
    
    <!-- 主内容层 -->
    <div class="content-overlay">
      <!-- 直接显示在视频上的标题 -->
      <h1 class="main-title">视频空间大数据平台</h1>
      
      <div class="app-container">
        <div class="connection-status">
          <div class="status-indicator" :class="{ connected: isConnected }"></div>
          <div>{{ connectionStatus }}</div>
        </div>
          
        <div class="video-container">
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
          
          <!-- 滚动区域容器 -->
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
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

// 添加滚动区域的引用
const scrollableArea = ref(null)

// 计算左侧视频容器的高度
const calculateScrollHeight = () => {
  const videoContainer = document.querySelector('.video-container')
  const sectionTitle = document.querySelector('.annotations-section .section-title')
  const annotationInput = document.querySelector('.annotation-input')
  const saveAllBtn = document.querySelector('.save-all-btn')
  const statusBar = document.querySelector('.status-bar')
  if (!videoContainer || !sectionTitle || !annotationInput || !saveAllBtn || !statusBar || !scrollableArea.value) return
  
  // 获取左侧视频容器的高度
  const videoHeight = videoContainer.clientHeight
  const sectionTitleHeight = sectionTitle.offsetHeight
  const annotationInputHeight = annotationInput.offsetHeight
  const saveAllBtnHeight = saveAllBtn.offsetHeight
  const statusBarHeight = statusBar.offsetHeight
  // 计算可滚动区域的高度 = 视频容器高度 - 标题高度 - 输入框高度 - 保存按钮高度 - 状态栏高度 - 40(margin的高度)
  const scrollableHeight = videoHeight - sectionTitleHeight - annotationInputHeight - saveAllBtnHeight - statusBarHeight - 40
  
  // 设置滚动区域的最大高度
  scrollableArea.value.style.maxHeight = `${scrollableHeight}px`
}

// 引用Canvas元素
const videoCanvas = ref(null)
const annotationCanvas = ref(null)

// 状态管理
const isDrawing = ref(true) // 默认开启标注模式
const isActiveDrawing = ref(false) // 是否有活跃的未保存标注
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
  // 设置Canvas尺寸
  const container = document.querySelector('.video-container')
  videoCanvas.value.width = window.innerWidth
  videoCanvas.value.height = window.innerHeight
  annotationCanvas.value.width = container.clientWidth
  annotationCanvas.value.height = container.clientHeight
  
  // 获取上下文
  videoCtx = videoCanvas.value.getContext('2d')
  annotationCtx = annotationCanvas.value.getContext('2d')
  annotationCtx.lineWidth = 3
  
  drawCanvas()
}

// 建立WebSocket连接
const connectWebSocket = () => {
  // 替换为您的WebSocket服务器地址
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
      // 文本消息（如元数据）
      console.log('Received header:', event.data)
    } else {
      // 二进制数据（JPEG图像）
      frameCount.value++
      
      // 计算FPS
      const elapsed = (performance.now() - startTime.value) / 1000
      if (elapsed >= 1) {
        fps.value = frameCount.value / elapsed
        frameCount.value = 0
        startTime.value = performance.now()
      }
      
      // 处理图像
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
      videoCtx.drawImage(img, 0, 0, videoCtx.canvas.width, videoCtx.canvas.height)
    }
    URL.revokeObjectURL(url)
    drawCanvas()
  }
  
  img.src = url
}

// 鼠标按下事件处理
const handleMouseDown = (e) => {
  if (!isDrawing.value) return
  
  // 开始新绘制时清除前一个未保存的标注
  if (isActiveDrawing.value) {
    currentAnnotation.value.rect = { x: 0, y: 0, width: 0, height: 0 }
  }
  
  isActiveDrawing.value = true

  const rect = annotationCanvas.value.getBoundingClientRect()
  startX.value = e.clientX - rect.left
  startY.value = e.clientY - rect.top
  
  // 开始绘制
  annotationCanvas.value.addEventListener('mousemove', handleMouseMove)
  annotationCanvas.value.addEventListener('mouseup', handleMouseUp)
}

// 鼠标移动事件处理
const handleMouseMove = (e) => {
  const rect = annotationCanvas.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  
  // 计算矩形尺寸
  currentAnnotation.value.rect = {
    x: Math.min(startX.value, mouseX),
    y: Math.min(startY.value, mouseY),
    width: Math.abs(mouseX - startX.value),
    height: Math.abs(mouseY - startY.value)
  }

  // 绘制临时矩形
  drawCanvas()
}

// 鼠标释放事件处理
const handleMouseUp = () => {
  // 移除事件监听
  annotationCanvas.value.removeEventListener('mousemove', handleMouseMove)
  annotationCanvas.value.removeEventListener('mouseup', handleMouseUp)
  
  // 保持临时矩形显示直到保存或取消
  drawCanvas()
}

// 绘制Canvas（标注框和已有标注）
const drawCanvas = () => {
  if (!annotationCtx) return
  
  // 清除画布
  annotationCtx.clearRect(0, 0, annotationCtx.canvas.width, annotationCtx.canvas.height)

  
  // 绘制临时矩形（用户正在绘制的或已绘制但未保存的）
  if (isActiveDrawing.value && currentAnnotation.value.rect.width > 0 && currentAnnotation.value.rect.height > 0) {
    annotationCtx.strokeStyle = '#FF5722'
    annotationCtx.setLineDash([5, 5])
    annotationCtx.strokeRect(
      currentAnnotation.value.rect.x,
      currentAnnotation.value.rect.y,
      currentAnnotation.value.rect.width,
      currentAnnotation.value.rect.height
    )
    annotationCtx.setLineDash([])
  }
  
  // 绘制已保存的标注
  annotations.value.forEach(anno => {
    // 添加半透明填充效果（标注框内部区域）
    annotationCtx.fillStyle = 'rgba(0, 123, 255, 0.2)' // 蓝色
    annotationCtx.fillRect(
      anno.rect.x,
      anno.rect.y,
      anno.rect.width,
      anno.rect.height
    )
    annotationCtx.strokeStyle = '#007BFF'
    annotationCtx.lineWidth = 2
    
    annotationCtx.strokeRect(
      anno.rect.x,
      anno.rect.y,
      anno.rect.width,
      anno.rect.height
    )

    // 设置25px字体大小
    annotationCtx.font = 'bold 25px Arial'
    const text = anno.text
    const textWidth = annotationCtx.measureText(text).width

   // 计算文本背景框尺寸 - 高度设为30px以适应25px字体
    const textHeight = 30
    const padding = 10

    // 绘制标注文本背景
    annotationCtx.fillStyle = 'rgba(0, 123, 255, 0.7)'
    annotationCtx.fillRect(
      anno.rect.x,
      anno.rect.y - textHeight,
      textWidth + padding * 2,  // 两侧各加10px内边距
      textHeight
    )
    
    // 绘制标注文本
    annotationCtx.fillStyle = 'white'
    annotationCtx.textBaseline = 'middle' // 垂直居中
    annotationCtx.fillText(
      text,
      anno.rect.x + padding, // 水平位置加10px内边距
      anno.rect.y - textHeight / 2 // 垂直居中
    )
  })
}

// 保存标注
const saveAnnotation = () => {
  if (currentAnnotation.value.text.trim() !== '' && 
      currentAnnotation.value.rect.width > 0 && 
      currentAnnotation.value.rect.height > 0) {

    // 添加唯一ID
    const annotationWithId = {
      ...currentAnnotation.value,
      id: 'anno-' + Date.now().toString(36)
    }
    
    annotations.value.push(annotationWithId)
    
    // 重置状态
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

  // 添加事件监听
  if (annotationCanvas.value) {
    annotationCanvas.value.addEventListener('mousedown', handleMouseDown)
  }
  
  // 窗口大小改变时重新初始化Canvas
  window.addEventListener('resize', initCanvas)

  calculateScrollHeight()
  
  // 监听窗口大小变化
  window.addEventListener('resize', calculateScrollHeight)
  
  // 监听标注数量变化
  watch(annotations, () => {
    nextTick(calculateScrollHeight)
  })
})

onUnmounted(() => {
  // 关闭WebSocket连接
  if (socket) {
    socket.close()
  }
  
  // 移除事件监听
  window.removeEventListener('resize', initCanvas)
  
  if (annotationCanvas.value) {
    annotationCanvas.value.removeEventListener('mousedown', handleMouseDown)
  }

  window.removeEventListener('resize', calculateScrollHeight)
})
</script>

<style scoped>
.annotator-container {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

/* 视频背景层 */
.video-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.video-background canvas {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 内容覆盖层 */
.content-overlay {
  position: relative;
  z-index: 2;
  height: 100%;
}

/* 主标题样式 */
.main-title {
  position: absolute;
  top: 30px;
  left: 0;
  width: 100%;
  text-align: center;
  color: white;
  font-size: 2.8rem;
  font-weight: bold;
  text-shadow: 
    0 0 10px rgba(0, 0, 0, 0.8),
    0 0 20px rgba(0, 0, 0, 0.6),
    0 0 30px rgba(0, 0, 0, 0.4);
  z-index: 10;
  letter-spacing: 2px;
  pointer-events: none;
}

.app-container {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 20px;
  padding: 20px;
  height: 100%;
}

.video-container {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

#annotationCanvas {
  cursor: crosshair;
}

.annotations-section {
  background: rgba(17, 24, 39, 0.85);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.section-title {
  font-size: 1.5rem;
  margin-bottom: 15px;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(59, 130, 246, 0.5);
  text-align: center;
  color: #3b82f6;
  font-weight: bold;
}

.annotation-input {
  margin-bottom: 20px;
  background: rgba(31, 41, 55, 0.7);
  border-radius: 10px;
  padding: 15px;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.annotation-input h3 {
  color: #93c5fd;
  margin-bottom: 10px;
}

.annotation-input textarea {
  width: 100%;
  padding: 12px;
  margin: 10px 0;
  border-radius: 8px;
  background: rgba(17, 24, 39, 0.8);
  color: white;
  border: 1px solid rgba(59, 130, 246, 0.3);
  resize: vertical;
  font-family: inherit;
}

.annotation-input textarea:focus {
  outline: 2px solid #3b82f6;
}

.input-buttons {
  display: flex;
  gap: 15px;
  margin-top: 10px;
}

.save-btn {
  padding: 12px 15px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  width: 100%;
  font-size: 1rem;
}

.cancel-btn {
  padding: 12px 15px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(90deg, #6b7280, #4b5563);
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
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
}

.save-all-btn {
  padding: 14px 20px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  width: 100%;
  margin-top: 15px;
  font-size: 1.1rem;
}

.save-all-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
  background: linear-gradient(90deg, #1d4ed8, #3b82f6);
}

/* 新增的滚动区域容器 */
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
  padding-right: 5px;
}

/* 滚动条样式 */
.annotation-list::-webkit-scrollbar {
  width: 8px;
}

.annotation-list::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.5);
  border-radius: 4px;
}

.annotation-list::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.7);
  border-radius: 4px;
}

.annotation-list::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.9);
}

.annotation-item {
  background: rgba(31, 41, 55, 0.7);
  border-radius: 10px;
  padding: 15px;
  margin-bottom: 15px;
  border-left: 4px solid #3b82f6;
  transition: all 0.3s;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

.annotation-item:hover {
  background: rgba(55, 65, 81, 0.8);
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
}

.annotation-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.annotation-id {
  font-weight: bold;
  color: #93c5fd;
  font-size: 1.1rem;
}

.annotation-position {
  font-size: 0.95rem;
  opacity: 0.9;
  margin-bottom: 10px;
  color: #c7d2fe;
}

.annotation-content {
  line-height: 1.5;
  padding: 12px 0;
  border-top: 1px dashed rgba(147, 197, 253, 0.3);
  color: #e5e7eb;
  font-size: 1.05rem;
}

.annotation-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 12px;
}

.action-btn {
  padding: 8px 15px;
  border-radius: 6px;
  background: rgba(55, 65, 81, 0.8);
  border: none;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.95rem;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.action-btn:hover {
  background: rgba(75, 85, 99, 0.9);
}

.delete-btn {
  background: rgba(220, 38, 38, 0.7);
}

.delete-btn:hover {
  background: rgba(220, 38, 38, 0.9);
}

.status-bar {
  display: flex;
  justify-content: space-between;
  padding: 12px 15px;
  background: rgba(17, 24, 39, 0.7);
  border-radius: 8px;
  font-size: 0.95rem;
  margin-top: auto;
  color: #c7d2fe;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.no-annotations {
  text-align: center;
  padding: 30px 0;
  opacity: 0.7;
  color: #9ca3af;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 15px;
  background: rgba(17, 24, 39, 0.8);
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  position: absolute;
  top: 100px;
  right: 380px;
  z-index: 5;
  color: #e5e7eb;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #ef4444;
}

.status-indicator.connected {
  background-color: #10b981;
}

@media (max-width: 900px) {
  .app-container {
    grid-template-columns: 1fr;
    height: auto;
  }
  
  .annotations-section {
    height: 500px;
  }
  
  .connection-status {
    right: 20px;
    top: 90px;
  }
  
  .main-title {
    font-size: 2.2rem;
    top: 20px;
  }
}
</style>