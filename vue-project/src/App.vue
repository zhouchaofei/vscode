<template>
  <div class="app-container">
    <header>
      <h1>智慧监管平台</h1>
      <!-- <p class="subtitle">在MP4视频上绘制标注框并添加说明文字，适用于视频分析、目标检测、教学讲解等多种场景</p> -->
    </header>
    
    <VideoAnnotator />
  </div>
</template>

<script>
import VideoAnnotator from './components/VideoAnnotator.vue'

export default {
  components: {
    VideoAnnotator
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #1a2a6c, #b21f1f, #1a2a6c);
  color: #fff;
  min-height: 100vh;
  padding: 20px;
}

.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

header {
  text-align: center;
  margin-bottom: 30px;
  padding: 20px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 15px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

h1 {
  font-size: 2.8rem;
  margin-bottom: 10px;
  background: linear-gradient(90deg, #ff8a00, #e52e71);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.subtitle {
  font-size: 1.2rem;
  opacity: 0.9;
  max-width: 700px;
  margin: 0 auto;
  line-height: 1.6;
}
</style>