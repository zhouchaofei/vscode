<template>
  <div class="video-playback">
    <div class="header">视频回放</div>
    <div class="controls">
      <div class="select-group">
        <label>选择摄像头：</label>
        <select v-model="selectedCamera">
          <option value="yn">永年</option>
          <option value="fx_n">肥乡北</option>
          <option value="fx_s">肥乡南</option>
          <option value="fx_lc">肥乡梁场</option>
        </select>
      </div>
      <div class="select-group">
        <label>选择日期：</label>
        <input type="date" v-model="selectedDate">
      </div>
      <button @click="playVideo" class="play-btn">回放</button>
    </div>
    <div class="video-container" v-if="videoSource">
      <video ref="videoPlayer" controls>
        <source :src="videoSource" :type="videoType">
        您的浏览器不支持视频播放。
      </video>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VideoPlayback',
  data() {
    return {
      selectedCamera: 'yn',
      selectedDate: new Date().toISOString().substr(0, 10),
      videoSource: '',
      videoType: 'video/mp4'
    }
  },
  methods: {
    playVideo() {
      if (!this.selectedCamera || !this.selectedDate) {
        alert('请选择摄像头和日期');
        return;
      }
      
      // Format date: YYYYMMDD
      const dateStr = this.selectedDate.replace(/-/g, '');
      
      // Construct video filename
      const filename = `${dateStr}${this.selectedCamera}.mp4`;
      
      // Set video source path - this will need adjustment based on how videos are served
      this.videoSource = `/videos/${filename}`;
      
      // Update video type based on file extension
      if (filename.endsWith('.mp4')) {
        this.videoType = 'video/mp4';
      } else if (filename.endsWith('.avi')) {
        this.videoType = 'video/x-msvideo';
      }
      
      // Play video after source is loaded
      this.$nextTick(() => {
        if (this.$refs.videoPlayer) {
          this.$refs.videoPlayer.load();
          this.$refs.videoPlayer.play();
        }
      });
    }
  }
}
</script>

<style scoped>
.video-playback {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
  box-sizing: border-box;
}

.header {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
}

.controls {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.select-group {
  margin-right: 20px;
  display: flex;
  align-items: center;
}

.select-group label {
  margin-right: 10px;
}

.play-btn {
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.play-btn:hover {
  background-color: #45a049;
}

.video-container {
  flex: 1;
  width: 100%;
  background-color: #000;
}

video {
  width: 100%;
  height: 100%;
  max-height: calc(100vh - 150px);
}
</style>