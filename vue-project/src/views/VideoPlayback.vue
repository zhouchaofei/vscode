<template>
  <div class="video-playback-container">
    <div class="header">视频回放</div>
    <div class="controls">
      <div class="select-group">
        <label for="camera-select">选择摄像头：</label>
        <select id="camera-select" v-model="selectedCamera">
          <option value="yn">永年</option>
          <option value="fx_n">肥乡北</option>
          <option value="fx_s">肥乡南</option>
          <option value="fx_lc">肥乡梁场</option>
        </select>
      </div>
      <div class="select-group">
        <label for="date-select">选择日期：</label>
        <input id="date-select" type="date" v-model="selectedDate">
      </div>
      <button @click="searchVideos" class="search-btn" :disabled="isLoading">
        {{ isLoading ? '搜索中...' : '搜索' }}
      </button>
    </div>
    <div class="main-content">
      <div class="video-list-panel">
        <div v-if="isLoading" class="list-message">正在加载视频列表...</div>
        <div v-else-if="!searched" class="list-message">请点击搜索按钮查找视频。</div>
        <div v-else-if="videoList.length === 0" class="list-message">未找到任何视频文件。</div>
        <ul v-else>
          <li
            v-for="video in videoList"
            :key="video.fileName"
            class="video-item"
            :class="{ active: currentVideoSource === video.src }"
            @click="selectVideo(video)"
          >
            <div class="video-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M10 16.5l6-4.5-6-4.5v9zM12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"></path></svg>
            </div>
            <div class="video-info">
              <span class="video-time">{{ video.displayTime }}</span>
              <span class="video-filename">{{ video.fileName }}</span>
            </div>
          </li>
        </ul>
      </div>
      <div class="video-player-area">
        <div v-if="!currentVideoSource" class="player-placeholder">
          请从左侧列表选择一个视频进行播放
        </div>
        <video
          v-else
          :key="currentVideoSource"
          ref="videoPlayer"
          controls
          muted 
          class="video-element"
        >
          <source :src="currentVideoSource" type="video/mp4">
          您的浏览器不支持视频播放。
        </video>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';

// --- 数据状态定义 ---
const selectedCamera = ref('yn');
const selectedDate = ref(getTodayDateString());
const videoList = ref([]);
const currentVideoSource = ref('');
const isLoading = ref(false);
const searched = ref(false);
const videoPlayer = ref(null);

// --- 方法定义 ---
function getTodayDateString() {
  const today = new Date();
  return today.toISOString().substr(0, 10);
}

async function searchVideos() {
  if (!selectedCamera.value || !selectedDate.value) {
    alert('请选择摄像头和日期');
    return;
  }
  isLoading.value = true;
  searched.value = true;
  videoList.value = [];
  currentVideoSource.value = '';

  const dateStr = selectedDate.value.replace(/-/g, '');
  
  try {
    const fileNames = await fetchVideoListFromServer(selectedCamera.value, dateStr);
    
    videoList.value = fileNames.map(fileName => ({
      fileName: fileName,
      src: `/videos/${dateStr}/${selectedCamera.value}/${fileName}`,
      displayTime: formatTimeFromFilename(fileName)
    }));

  } catch (error) {
    console.error("获取视频列表失败:", error);
    alert("获取视频列表失败，请检查网络或联系管理员。");
  } finally {
    isLoading.value = false;
  }
}

async function fetchVideoListFromServer(camera, date) {
  const apiUrl = `http://59.110.65.210:8081/videosData?location=${camera}&date=${date}`;
  try {
    const response = await fetch(apiUrl);
    if (!response.ok) {
      throw new Error(`网络请求失败，状态码: ${response.status}`);
    }
    const data = await response.json();
    return data.videos;
  } catch (error) {
    console.error("调用视频列表API时出错:", error);
    throw error;
  }
}

async function selectVideo(video) {
  currentVideoSource.value = video.src;
  try {
    await nextTick();
    if (videoPlayer.value) {
      await videoPlayer.value.play();
    }
  } catch (error) {
    console.warn("视频自动播放失败，这可能是浏览器策略导致的。用户需要手动点击播放。", error);
  }
}

function formatTimeFromFilename(fileName) {
  const parts = fileName.split('-');
  if (parts.length >= 7) {
    const startTimeStr = parts[4];
    const endTimeStr = parts[5];
    const format = (s) => s ? `${s.substr(8,2)}:${s.substr(10,2)}:${s.substr(12,2)}` : '';
    return `${format(startTimeStr)} - ${format(endTimeStr)}`;
  }
  return '未知时间';
}
</script>

<style scoped>
/* 样式部分无需改动 */
.video-playback-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 20px;
  box-sizing: border-box;
  background-color: #f0f2f5;
  color: #333;
}

.header {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.controls {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  background-color: #fff;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  flex-shrink: 0;
}

.select-group {
  margin-right: 20px;
  display: flex;
  align-items: center;
}

.select-group label {
  margin-right: 10px;
  font-weight: 500;
}

.select-group select, .select-group input {
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ccc;
}

.search-btn {
  padding: 8px 16px;
  background-color: #409EFF;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.search-btn:hover:not(:disabled) {
  background-color: #66b1ff;
}
.search-btn:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

.main-content {
  flex: 1;
  display: flex;
  gap: 20px;
  overflow: hidden;
}

.video-list-panel {
  width: 380px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  flex-shrink: 0;
}

.video-list-panel ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.list-message {
  padding: 20px;
  text-align: center;
  color: #888;
  margin: auto;
}

.video-item {
  display: flex;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #eef0f3;
  cursor: pointer;
  transition: background-color 0.2s;
}

.video-item:hover {
  background-color: #ecf5ff;
}

.video-item.active {
  background-color: #d9ecff;
}

.video-icon svg {
  width: 48px;
  height: 48px;
  color: #409EFF;
  margin-right: 15px;
}

.video-info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.video-time {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.video-filename {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 4px;
}

.video-player-area {
  flex: 1;
  background-color: #000;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.player-placeholder {
  color: #666;
  background-color: #2c2c2c;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 18px;
}

.video-element {
  width: 100%;
  height: 100%;
}
</style>