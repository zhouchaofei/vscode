<template>
  <div class="annotator-container">
    <div class="app-container">
      <div class="video-section">
        <h2 class="section-title">视频标注区域</h2>
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
        
        <!-- 添加滚动区域的容器 -->
        <div class="scrollable-area" ref="scrollableArea">
          <div class="annotation-list">
            <div v-if="annotations.length === 0" class="no-annotations">
              <p>尚未添加任何标注</p>
              <p>在视频上绘制矩形框并添加说明</p>
            </div>
            
            <div v-for="(annotation, index) in annotations" :key="annotation.id" class="annotation-item">
              <div class="annotation-header">
                <div class="annotation-id">标注 #{{ index + 1 }}</div>
                <!-- <div class="annotation-time">ID: {{ annotation.id.slice(0, 6) }}</div> -->
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
  videoCanvas.value.width = container.clientWidth
  videoCanvas.value.height = container.clientHeight
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
    annotationCtx.fillStyle = 'rgba(76, 175, 80, 0.2)' // 20% 透明度的绿色
    annotationCtx.fillRect(
      anno.rect.x,
      anno.rect.y,
      anno.rect.width,
      anno.rect.height
    )
    annotationCtx.strokeStyle = '#4CAF50'
    annotationCtx.lineWidth = 2
    // 使用半透明颜色增加模糊感
    // annotationCtx.strokeStyle = 'rgba(76, 175, 80, 0.7)'
    // annotationCtx.lineWidth = 3
    
    // 添加阴影效果增强模糊感
    // annotationCtx.shadowColor = 'rgba(76, 175, 80, 0.5)';
    // annotationCtx.shadowBlur = 5;

    annotationCtx.strokeRect(
      anno.rect.x,
      anno.rect.y,
      anno.rect.width,
      anno.rect.height
    )

    // 重置阴影效果
    annotationCtx.shadowColor = 'transparent';
    annotationCtx.shadowBlur = 0;
    
    // 设置25px字体大小
    annotationCtx.font = 'bold 25px Arial'
    const text = anno.text
    const textWidth = annotationCtx.measureText(text).width

   // 计算文本背景框尺寸 - 高度设为30px以适应25px字体
    const textHeight = 30
    const padding = 10

    // 绘制标注文本背景
    annotationCtx.fillStyle = 'rgba(76, 175, 80, 0.7)'
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

/* .controls {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: auto;
} */

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
  /* padding-bottom: 10px; */
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
  /* margin-bottom: 10px; */
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
  /* margin-top: 10px; */
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
  /* flex: 1; */
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
  /* margin-top: 15px; */
  font-size: 1.1rem;
}

.save-all-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

/* 新增的滚动区域容器 */
.scrollable-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 100%; /* 添加最大高度限制 */
}

.annotation-list {
  /* max-height: 600px; */
  overflow-y: auto;
  flex: 1;
}

/* 滚动条样式 */
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
  /* transform: translateX(5px); */
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
  /* margin-top: 20px; */
  padding: 10px 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  font-size: 0.9rem;
  margin-top: auto;/* 确保状态栏保持在底部 */
  flex-direction: column;
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
  /* margin-bottom: 15px; */
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
    height: 500px; /* 在移动设备上设置固定高度 */
  }
}
</style>