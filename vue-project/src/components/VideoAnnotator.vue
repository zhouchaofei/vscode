<template>
  <div class="annotator-container">
    <div class="app-container">
      <div class="video-section">
        <h2 class="section-title">视频标注区域</h2>
        <div class="video-container">
          <video ref="videoPlayer" :src="videoSource" @timeupdate="drawCanvas"></video>
          <canvas ref="canvas" @mousedown="handleMouseDown"></canvas>
        </div>
        
        <div class="controls">
          <button @click="togglePlay" class="btn">{{ isPlaying ? '暂停' : '播放' }}</button>
          <button @click="startDrawing" class="btn" :disabled="isDrawing">开始标注</button>
        </div>
        
      </div>
      
      <div class="annotations-section">
        <h2 class="section-title">标注列表</h2>
        
        <div v-if="isDrawing" class="annotation-input">
          <h3>添加标注说明</h3>
          <textarea v-model="currentAnnotation.text" placeholder="在此输入标注说明..." rows="4"></textarea>
          <div class="controls">
            <button @click="saveAnnotation" class="btn">保存标注</button>
            <button @click="cancelAnnotation" class="btn btn-danger">取消</button>
          </div>
        </div>
        
        <!-- 添加滚动区域的容器 -->
        <div class="scrollable-area">
          <div class="annotation-list">
            <div v-if="annotations.length === 0" class="no-annotations">
              <p>尚未添加任何标注</p>
              <!-- <p>点击"开始标注"按钮创建第一个标注</p> -->
            </div>
            
            <div v-for="(annotation, index) in annotations" :key="index" class="annotation-item">
              <div class="annotation-header">
                <!-- <div class="annotation-time">时间: {{ formatTime(annotation.time) }}</div> -->
                <div>标注 #{{ index + 1 }}</div>
              </div>
              <div class="annotation-position">
                <div>位置: ({{ annotation.rect.x.toFixed(0) }}, {{ annotation.rect.y.toFixed(0) }})</div>
                <!-- 位置: ({{ annotation.rect.x.toFixed(0) }}, {{ annotation.rect.y.toFixed(0) }}) -->
                <div>尺寸: {{ annotation.rect.width.toFixed(0) }}×{{ annotation.rect.height.toFixed(0) }}</div>
              </div>
              <div class="annotation-content">
                名称: {{ annotation.text }}
              </div>
              <div class="annotation-actions">
                <!-- 暂不需要查看 -->
                <!-- <button @click="goToAnnotation(annotation)" class="action-btn">查看</button> -->
                <button @click="deleteAnnotation(index)" class="action-btn delete-btn">删除</button>
              </div>
            </div>
          </div>
        </div>
        
        <div class="status-bar">
          <div>标注总数: {{ annotations.length }}</div>
          <!-- <div>当前状态: {{ isDrawing ? '标注中...' : (isPlaying ? '播放中' : '已暂停') }}</div> -->
        </div>
        <div class="controls">
          <button @click="clearCanvas" class="btn btn-danger">清除画布</button>
          <button @click="saveAllAnnotations" class="btn btn-secondary">保存所有标注</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// 视频源 - 实际项目中可替换为您的视频URL
const videoSource = ref('/src/assets/demo-video.mp4')

// 引用DOM元素
const videoPlayer = ref(null)
const canvas = ref(null)

// 状态管理
const isPlaying = ref(false)
const isDrawing = ref(false)
const currentAnnotation = ref({
  rect: { x: 0, y: 0, width: 0, height: 0 },
  text: '',
  time: 0
})
const annotations = ref([])
const ctx = ref(null)

// 绘制状态变量
const startX = ref(0)
const startY = ref(0)
const drawingRect = ref({ x: 0, y: 0, width: 0, height: 0 })

// 初始化Canvas
const initCanvas = () => {
  if (canvas.value && videoPlayer.value) {
    canvas.value.width = videoPlayer.value.offsetWidth
    canvas.value.height = videoPlayer.value.offsetHeight
    ctx.value = canvas.value.getContext('2d')
    ctx.value.lineWidth = 3
    drawCanvas()// 初始绘制
  }
}

// 播放/暂停视频
const togglePlay = () => {
  if (isPlaying.value) {
    videoPlayer.value.pause()
  } else {
    videoPlayer.value.play()
  }
  isPlaying.value = !isPlaying.value
}

// 开始绘制标注框
const startDrawing = () => {
  isDrawing.value = true
  canvas.value.style.cursor = 'crosshair'
}

// 鼠标按下事件处理
const handleMouseDown = (e) => {
  if (!isDrawing.value) return
  
  const rect = canvas.value.getBoundingClientRect()
  startX.value = e.clientX - rect.left
  startY.value = e.clientY - rect.top
  
  // 开始绘制
  canvas.value.addEventListener('mousemove', handleMouseMove)
  canvas.value.addEventListener('mouseup', handleMouseUp)
}

// 鼠标移动事件处理
const handleMouseMove = (e) => {
  const rect = canvas.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  
  // 计算矩形尺寸
  drawingRect.value = {
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
  canvas.value.removeEventListener('mousemove', handleMouseMove)
  canvas.value.removeEventListener('mouseup', handleMouseUp)
  
  // 保存绘制的矩形
  currentAnnotation.value.rect = { ...drawingRect.value }
  currentAnnotation.value.time = videoPlayer.value.currentTime
  
  // 重置临时矩形
  drawingRect.value = { x: 0, y: 0, width: 0, height: 0 }
}

// 绘制Canvas（标注框和已有标注）
const drawCanvas = () => {
  if (!ctx.value) return
  
  // 清除画布
  ctx.value.clearRect(0, 0, canvas.value.width, canvas.value.height)
  
  // 绘制临时矩形（用户正在绘制的）
  if (isDrawing.value && drawingRect.value.width > 0 && drawingRect.value.height > 0) {
    ctx.value.strokeStyle = '#FF5722'
    ctx.value.setLineDash([5, 5])
    ctx.value.strokeRect(
      drawingRect.value.x,
      drawingRect.value.y,
      drawingRect.value.width,
      drawingRect.value.height
    )
    ctx.value.setLineDash([])
  }
  
  // 绘制已保存的标注
  annotations.value.forEach(anno => {
    ctx.value.strokeStyle = '#4CAF50'
    ctx.value.strokeRect(
      anno.rect.x,
      anno.rect.y,
      anno.rect.width,
      anno.rect.height
    )
    
    // 绘制标注文本背景
    ctx.value.fillStyle = 'rgba(76, 175, 80, 0.7)'
    const textWidth = ctx.value.measureText(anno.text).width
    ctx.value.fillRect(
      anno.rect.x,
      anno.rect.y - 20,
      textWidth + 10,
      20
    )
    
    // 绘制标注文本
    ctx.value.fillStyle = 'white'
    ctx.value.font = '14px Arial'
    ctx.value.fillText(
      anno.text,
      anno.rect.x + 5,
      anno.rect.y - 5
    )
  })
}

// 保存标注
const saveAnnotation = () => {
  if (currentAnnotation.value.text.trim() !== '') {
    annotations.value.push({ ...currentAnnotation.value })
    currentAnnotation.value.text = ''
    isDrawing.value = false
    canvas.value.style.cursor = 'default'
    drawCanvas()
  }
}

// 取消标注
const cancelAnnotation = () => {
  isDrawing.value = false
  currentAnnotation.value.text = ''
  drawingRect.value = { x: 0, y: 0, width: 0, height: 0 }
  canvas.value.style.cursor = 'default'
  drawCanvas()
}

// 清除画布
const clearCanvas = () => {
  if (ctx.value) {
    ctx.value.clearRect(0, 0, canvas.value.width, canvas.value.height)
  }
}

// 删除标注
const deleteAnnotation = (index) => {
  annotations.value.splice(index, 1)
  drawCanvas()
}

// 跳转到标注时间点
const goToAnnotation = (annotation) => {
  videoPlayer.value.currentTime = annotation.time
  if (!isPlaying.value) {
    videoPlayer.value.play()
    isPlaying.value = true
  }
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

// 格式化时间
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 生命周期钩子
onMounted(() => {
  initCanvas()
  
  // 窗口大小改变时重新初始化Canvas
  window.addEventListener('resize', initCanvas)
  
  // 视频播放结束
  if (videoPlayer.value) {
    videoPlayer.value.addEventListener('ended', () => {
      isPlaying.value = false
    })
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', initCanvas)
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
  padding-top: 56.25%; /* 16:9 Aspect Ratio */
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.5);
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
  cursor: default;
}

.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: auto;
}

.btn {
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(90deg, #ff8a00, #e52e71);
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  flex: 1;
  min-width: 120px;
}

.btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.btn:active {
  transform: translateY(1px);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: linear-gradient(90deg, #4776E6, #8E54E9);
}

.btn-danger {
  background: linear-gradient(90deg, #ff416c, #ff4b2b);
}

.annotations-section {
  background: rgba(0, 0, 0, 0.4);
  border-radius: 15px;
  padding: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  height: fit-content;
}

.section-title {
  font-size: 1.5rem;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 2px solid rgba(255, 255, 255, 0.2);
  text-align: center;
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
}

/* 新增的滚动区域容器 */
.scrollable-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  /* margin-bottom: 15px; */
  max-height: 700px;
}

.annotation-list {
  /* max-height: 400px; */
  overflow-y: auto;
  padding-right: 10px;
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
  padding: 15px;
  margin-bottom: 15px;
  border-left: 4px solid #ff8a00;
  transition: all 0.3s;
}

.annotation-item:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateX(5px);
}

.annotation-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.annotation-time {
  font-weight: bold;
  color: #ff8a00;
}

.annotation-content {
  margin-top: 8px;
  line-height: 1.5;
}

.annotation-actions {
  display: flex;
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
  padding: 10px 15px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  font-size: 0.9rem;
  margin-top: auto;/* 确保状态栏保持在底部 */
}

.instructions {
  background: rgba(0, 0, 0, 0.3);
  padding: 15px;
  border-radius: 10px;
  margin-top: 25px;
  font-size: 0.95rem;
  line-height: 1.6;
}

.instructions h3 {
  margin-bottom: 10px;
  color: #ff8a00;
}

.instructions ul {
  padding-left: 20px;
}

.instructions li {
  margin-bottom: 8px;
}

.no-annotations {
  text-align: center;
  padding: 30px 0;
  opacity: 0.7;
}

@media (max-width: 900px) {
  .app-container {
    grid-template-columns: 1fr;
    height: auto;
  }
  
  .controls {
    flex-direction: column;
  }

  .annotations-section {
    height: 500px; /* 在移动设备上设置固定高度 */
  }
}
</style>