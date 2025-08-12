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
          muted class="video-element"
        >
          <source :src="currentVideoSource" type="video/mp4">
          您的浏览器不支持视频播放。
        </video>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VideoPlayback',
  data() {
    return {
      selectedCamera: 'yn',
      selectedDate: this.getTodayDateString(),
      videoList: [],
      currentVideoSource: '',
      isLoading: false,
      searched: false, // 用于跟踪是否已经执行过搜索
    }
  },
  methods: {
    getTodayDateString() {
      const today = new Date();
      return today.toISOString().substr(0, 10);
    },
    
    // --- 关键函数：搜索视频 ---
    async searchVideos() {
      if (!this.selectedCamera || !this.selectedDate) {
        alert('请选择摄像头和日期');
        return;
      }
      this.isLoading = true;
      this.searched = true;
      this.videoList = []; // 清空上一次的列表
      this.currentVideoSource = ''; // 清空播放器

      const dateStr = this.selectedDate.replace(/-/g, '');
      
      try {
        const fileNames = await this.fetchVideoListFromServer(this.selectedCamera, dateStr);
        
        this.videoList = fileNames.map(fileName => {
          return {
            fileName: fileName,
            src: `/videos/${dateStr}/${this.selectedCamera}/${fileName}`,
            displayTime: this.formatTimeFromFilename(fileName)
          };
        });

      } catch (error) {
        console.error("获取视频列表失败:", error);
        alert("获取视频列表失败，请检查网络或联系管理员。");
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * !!! 已更新：此函数现在调用真实的后端API !!!
     * @param {string} camera - 摄像头ID, e.g., 'yn'
     * @param {string} date - 日期字符串, e.g., '20250803'
     * @returns {Promise<string[]>} - 返回一个包含文件名的数组
     */
    async fetchVideoListFromServer(camera, date) {
      // 1. 构建完整的API URL
      const apiUrl = `http://59.110.65.210:8081/videosData?location=${camera}&date=${date}`;
      console.log(`正在从API获取视频列表: ${apiUrl}`);

      try {
        // 2. 使用 fetch 发送网络请求
        const response = await fetch(apiUrl);

        // 3. 检查请求是否成功 (HTTP状态码 200-299)
        if (!response.ok) {
          // 如果不成功，抛出错误，外层的catch会捕获到
          throw new Error(`网络请求失败，状态码: ${response.status}`);
        }

        // 4. 将返回的 body 解析为 JSON 格式
        //    我们假设API会返回一个文件名的数组，例如: ["file1.mp4", "file2.mp4"]
        const fileNames = await response.json();
        return fileNames;

      } catch (error) {
        // 5. 如果发生任何错误（网络问题、服务器崩溃等），在控制台打印并向上抛出
        console.error("调用视频列表API时出错:", error);
        throw error; // 将错误抛出，让调用此函数的地方（searchVideos方法）可以捕获并处理
      }
    },

    // --- 点击列表项时，更新播放器源 ---
    async selectVideo(video) {
      this.currentVideoSource = video.src;
      try {
        // this.$nextTick 确保Vue已经根据新的currentVideoSource更新了DOM
        await this.$nextTick(); 
        
        // 现在可以安全地访问更新后的 videoPlayer 元素并播放它
        if (this.$refs.videoPlayer) {
          // .play() 方法会返回一个Promise，我们await它
          await this.$refs.videoPlayer.play();
        }
      } catch (error) {
        // 如果自动播放失败（例如被浏览器策略阻止），会在控制台打印警告
        console.warn("视频自动播放失败，这可能是浏览器策略导致的。用户需要手动点击播放。", error);
      }
    },

    // --- 从长文件名中提取并格式化时间 ---
    formatTimeFromFilename(fileName) {
      const parts = fileName.split('-');
      if (parts.length >= 7) {
        const startTimeStr = parts[4]; // e.g., "20250803055953"
        const endTimeStr = parts[5];   // e.g., "20250803062949"
        
        const format = (s) => `${s.substr(8,2)}:${s.substr(10,2)}:${s.substr(12,2)}`;

        return `${format(startTimeStr)} - ${format(endTimeStr)}`;
      }
      return '未知时间';
    }
  }
}
</script>

<style scoped>
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
  overflow: hidden; /* 防止子元素溢出 */
}

.video-list-panel {
  width: 380px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  overflow-y: auto; /* 让列表内容可滚动 */
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