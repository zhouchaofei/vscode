<template>
  <div class="annotator-container">
    <div class="app-container">
      <div class="video-section">
        <h2 class="section-title">视频标注区域</h2>
        
        <div class="video-container">
          <video ref="videoPlayer" :src="videoSource" autoplay muted playsinline></video>
          <canvas ref="canvas"></canvas>
        </div>
        
        <div class="instructions">
          <h3>操作指南：</h3>
          <ul>
            <li>按住鼠标左键在视频上<strong>拖动绘制矩形框</strong></li>
            <li>在右侧输入标注信息并点击<strong>保存标注</strong></li>
            <li>标注框会<strong>持续显示</strong>在视频上</li>
            <li>点击标注列表中的<strong>删除按钮</strong>可移除标注</li>
            <li>使用<strong>保存所有标注</strong>按钮导出标注数据</li>
          </ul>
        </div>
      </div>
      
      <div class="annotations-section">
        <h2 class="section-title">标注管理</h2>
        
        <div class="annotation-input">
          <h3>添加标注说明</h3>
          <textarea v-model="currentAnnotation.text" placeholder="在此输入标注说明..." rows="4"></textarea>
          <div class="input-buttons">
            <button @click="saveAnnotation" class="save-btn">保存标注</button>
            <button @click="cancelAnnotation" class="cancel-btn">取消</button>
          </div>
        </div>
        
        <div class="scrollable-area">
          <div class="annotation-list">
            <div v-if="annotations.length === 0" class="no-annotations">
              <p>尚未添加任何标注</p>
              <p>在视频上绘制矩形框并添加说明</p>
            </div>
            
            <div v-for="(annotation, index) in annotations" :key="annotation.id" class="annotation-item">
              <div class="annotation-header">
                <div class="annotation-id">标注 #{{ index + 1 }}</div>
                <div class="annotation-time">ID: {{ annotation.id.slice(0, 6) }}</div>
              </div>
              <div class="annotation-position">
                位置: ({{ annotation.rect.x.toFixed(0) }}, {{ annotation.rect.y.toFixed(0) }})
                尺寸: {{ annotation.rect.width.toFixed(0) }}×{{ annotation.rect.height.toFixed(0) }}
              </div>
              <div class="annotation-content">
                {{ annotation.text }}
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
          <div>当前时间: {{ formatTime(videoCurrentTime) }}</div>
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
const isDrawing = ref(true) // 默认开启标注模式
const currentAnnotation = ref({
  rect: { x: 0, y: 0, width: 0, height: 0 },
  text: ''
})
const annotations = ref([])
const ctx = ref(null)
const videoCurrentTime = ref(0)

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
    drawCanvas()
  }
}

// 自动播放视频
const playVideo = () => {
  if (videoPlayer.value) {
    videoPlayer.value.play()
      .catch(error => {
        console.log("视频自动播放失败:", error)
        // 对于某些浏览器需要用户交互才能自动播放
        // 这里可以添加一个提示让用户点击播放
      })
  }
}

// 更新视频当前时间
const updateVideoTime = () => {
  if (videoPlayer.value) {
    videoCurrentTime.value = videoPlayer.value.currentTime
  }
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
    ctx.value.lineWidth = 2
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
    // 添加唯一ID
    const annotationWithId = {
      ...currentAnnotation.value,
      id: 'anno-' + Date.now().toString(36)
    }
    
    annotations.value.push(annotationWithId)
    currentAnnotation.value.text = ''
    drawCanvas()
  }
}

// 取消标注
const cancelAnnotation = () => {
  currentAnnotation.value.text = ''
  drawingRect.value = { x: 0, y: 0, width: 0, height: 0 }
  drawCanvas()
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

// 格式化时间
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 生命周期钩子
onMounted(() => {
  initCanvas()
  playVideo()
  
  // 添加事件监听
  if (canvas.value) {
    canvas.value.addEventListener('mousedown', handleMouseDown)
  }
  
  // 窗口大小改变时重新初始化Canvas
  window.addEventListener('resize', initCanvas)
  
  // 视频时间更新时重绘画布
  if (videoPlayer.value) {
    videoPlayer.value.addEventListener('timeupdate', () => {
      updateVideoTime()
      drawCanvas()
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
}

.app-container {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 25px;
  height: calc(100vh - 180px);
}

.video-section {
  background: rgba(0, 0, 0, 0.4);
  border-radius: 15px;
  padding: 20px;
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
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
  background: #000;
  margin-bottom: 15px;
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

.instructions {
  background: rgba(0, 0, 0, 0.3);
  padding: 15px;
  border-radius: 10px;
  margin-top: auto;
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

.annotations-section {
  background: rgba(0, 0, 0, 0.4);
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.section-title {
  font-size: 1.5rem;
  margin-bottom: 20px;
  padding-bottom: 10px;
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
  margin-bottom: 10px;
  color: #ff8a00;
}

.annotation-input textarea {
  width: 100%;
  padding: 12px;
  margin: 10px 0;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
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
  margin-top: 10px;
}

.save-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(90deg, #ff8a00, #e52e71);
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  flex: 1;
  font-size: 1rem;
}

.cancel-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(90deg, #4776E6, #8E54E9);
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  flex: 1;
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
  margin-top: 15px;
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
  margin-bottom: 15px;
}

.annotation-list {
  overflow-y: auto;
  padding-right: 8px;
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
  padding: 10px 15px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  font-size: 0.9rem;
  margin-top: auto;
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
  
  .annotations-section {
    height: 500px;
  }
}
</style>