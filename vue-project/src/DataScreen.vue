<template>
  <div class="data-screen-container">
    <!-- 1. 背景和带动画效果的头部 -->
    <div class="screen-header">
      <div class="header-lf">
        <span class="header-screening" v-show="false">首页</span>
      </div>
      <div class="header-ct">
        <div class="header-title">
          <span class="title-text">智慧监管平台</span>
          <!-- 标题装饰线条 -->
          <div class="header-title-decoration">
            <div class="line-left"></div>
            <div class="line-right"></div>
          </div>
        </div>
      </div>
      <div class="header-rg">
        <span class="header-download">{{ time }}</span>
      </div>
    </div>

    <!-- 2. 具有网格布局的主要内容区域 -->
    <div class="screen-content">
      <div class="screen-left">
        <div class="progress-panel">
          <div class="panel-title">永年北互通施工进度</div>
          <div class="construction-progress">
            <div class="progress-item" v-for="(item, index) in yongnianData" :key="index">
              <div class="item-title">{{ item.name }}</div>
              <div class="process-list">
                <div class="process-item" v-for="(process, pIndex) in item.processes" :key="pIndex">
                  <span class="process-name">{{ process.name }}：</span>
                  <div class="process-bar">
                    <div class="bar-inner" :style="{ width: process.percentage + '%' }"></div>
                  </div>
                  <span class="process-percentage">
                    <template v-if="item.name.includes('桥')">
                      {{ process.completed }}m/{{ process.total }}m ({{ process.percentage }}%)
                    </template>
                    <template v-else-if="item.name.includes('匝道')">
                      {{ process.percentage }}%
                    </template>
                    <template v-else>
                      {{ process.completed }}m/{{ process.total }}m ({{ process.percentage }}%)
                    </template>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="screen-center">
        <div class="center-top">
          <div class="center-title">实时监控</div>
          <div class="camera-container">
            <div
              v-for="(camera, index) in cameras"
              :key="index"
              class="camera-item"
              @click="openAnnotation(camera)"
            >
              <div class="camera-title">{{ camera.name }}</div>
              <div class="video-container" :id="`video-container-${index}`"></div>
            </div>
          </div>
        </div>
        <div class="center-bottom">
          <div class="warning-container">
            <div class="warning-title">安全预警信息</div>
            <div class="warning-content">
              <div class="warning-item">
                <div class="warning-icon">
                  <i class="el-icon-warning"></i>
                </div>
                <div class="warning-text">
                  <span class="warning-type">未佩戴安全帽：</span>
                  <span class="warning-count">{{ warningData.helmetMissing }} 次</span>
                </div>
              </div>
              <div class="warning-item">
                <div class="warning-icon">
                  <i class="el-icon-warning"></i>
                </div>
                <div class="warning-text">
                  <span class="warning-type">人员闯入吊装区：</span>
                  <span class="warning-count">{{ warningData.unauthorizedEntry }} 次</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="screen-right">
        <div class="progress-panel">
          <div class="panel-title">肥乡西互通施工进度</div>
          <div class="construction-progress">
            <div class="progress-item" v-for="(item, index) in feixiangData" :key="index">
              <div class="item-title">{{ item.name }}</div>
              <div class="process-list">
                <div class="process-item" v-for="(process, pIndex) in item.processes" :key="pIndex">
                  <span class="process-name">{{ process.name }}：</span>
                  <div class="process-bar">
                    <div class="bar-inner" :style="{ width: process.percentage + '%' }"></div>
                  </div>
                  <span class="process-percentage">
                    <template v-if="item.name.includes('桥')">
                      {{ process.completed }}m/{{ process.total }}m ({{ process.percentage }}%)
                    </template>
                    <template v-else-if="item.name.includes('匝道')">
                      {{ process.percentage }}%
                    </template>
                    <template v-else>
                      {{ process.completed }}m/{{ process.total }}m ({{ process.percentage }}%)
                    </template>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, onMounted, onBeforeUnmount, ref } from 'vue';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';

export default defineComponent({
  name: 'DataScreen',
  setup() {
    const time = ref('');
    const warningData = ref({
      helmetMissing: 15,
      unauthorizedEntry: 8
    });

    // 永年北互通数据
    const yongnianData = ref([
      {
        name: 'A匝道',
        processes: [
          { name: '挖台阶', completed: 280, total: 350, percentage: 80 },
          { name: '粉煤灰', completed: 250, total: 350, percentage: 71 },
          { name: '水泥稳定碎石', completed: 220, total: 350, percentage: 63 },
          { name: '沥青砼底面层', completed: 200, total: 350, percentage: 57 },
          { name: '沥青砼表面层', completed: 150, total: 350, percentage: 43 }
        ]
      },
      {
        name: '通道',
        processes: [
          { name: '基础开挖', completed: 150, total: 180, percentage: 83 },
          { name: '底板浇筑', completed: 130, total: 180, percentage: 72 },
          { name: '侧墙施工', completed: 100, total: 180, percentage: 56 },
          { name: '顶板施工', completed: 80, total: 180, percentage: 44 }
        ]
      },
      {
        name: '桥梁',
        processes: [
          { name: '桩基施工', completed: 400, total: 450, percentage: 89 },
          { name: '承台施工', completed: 380, total: 450, percentage: 84 },
          { name: '墩柱施工', completed: 320, total: 450, percentage: 71 },
          { name: '上部结构', completed: 250, total: 450, percentage: 56 }
        ]
      },
      {
        name: '通道2',
        processes: [
          { name: '基础开挖', completed: 160, total: 190, percentage: 84 },
          { name: '底板浇筑', completed: 140, total: 190, percentage: 74 },
          { name: '侧墙施工', completed: 110, total: 190, percentage: 58 },
          { name: '顶板施工', completed: 90, total: 190, percentage: 47 }
        ]
      },
      {
        name: '桥梁2',
        processes: [
          { name: '桩基施工', completed: 410, total: 460, percentage: 89 },
          { name: '承台施工', completed: 390, total: 460, percentage: 85 },
          { name: '墩柱施工', completed: 330, total: 460, percentage: 72 },
          { name: '上部结构', completed: 260, total: 460, percentage: 57 }
        ]
      }
    ]);

    // 肥乡西互通数据
    const feixiangData = ref([
      {
        name: 'B匝道',
        processes: [
          { name: '挖台阶', completed: 300, total: 380, percentage: 79 },
          { name: '粉煤灰', completed: 270, total: 380, percentage: 71 },
          { name: '水泥稳定碎石', completed: 240, total: 380, percentage: 63 },
          { name: '沥青砼底面层', completed: 210, total: 380, percentage: 55 },
          { name: '沥青砼表面层', completed: 180, total: 380, percentage: 47 }
        ]
      },
      {
        name: '涵洞',
        processes: [
          { name: '基础开挖', completed: 180, total: 200, percentage: 90 },
          { name: '底板浇筑', completed: 160, total: 200, percentage: 80 },
          { name: '侧墙施工', completed: 140, total: 200, percentage: 70 },
          { name: '顶板施工', completed: 120, total: 200, percentage: 60 }
        ]
      },
      {
        name: '立交桥',
        processes: [
          { name: '桩基施工', completed: 420, total: 480, percentage: 88 },
          { name: '承台施工', completed: 390, total: 480, percentage: 81 },
          { name: '墩柱施工', completed: 350, total: 480, percentage: 73 },
          { name: '上部结构', completed: 280, total: 480, percentage: 58 }
        ]
      },
      {
        name: 'C匝道',
        processes: [
          { name: '挖台阶', completed: 320, total: 390, percentage: 82 },
          { name: '粉煤灰', completed: 290, total: 390, percentage: 74 },
          { name: '水泥稳定碎石', completed: 260, total: 390, percentage: 67 },
          { name: '沥青砼底面层', completed: 230, total: 390, percentage: 59 },
          { name: '沥青砼表面层', completed: 190, total: 390, percentage: 49 }
        ]
      },
      {
        name: '跨线桥',
        processes: [
          { name: '桩基施工', completed: 430, total: 490, percentage: 88 },
          { name: '承台施工', completed: 400, total: 490, percentage: 82 },
          { name: '墩柱施工', completed: 360, total: 490, percentage: 73 },
          { name: '上部结构', completed: 290, total: 490, percentage: 59 }
        ]
      }
    ]);

    // 摄像头数据
    const cameras = ref([
      { id: 1, name: '摄像头1', url: 'http://example.com/video/view1_camera1', view: 'view1' },
      { id: 2, name: '摄像头2', url: 'http://example.com/video/view1_camera2', view: 'view1' },
      { id: 3, name: '摄像头3', url: 'http://example.com/video/view1_camera3', view: 'view1' },
      { id: 4, name: '摄像头4', url: 'http://example.com/video/view1_camera4', view: 'view1' }
    ]);

    let timerId = null;
    let players = [];

    // 更新时间
    const updateTime = () => {
      const date = new Date();
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      const seconds = String(date.getSeconds()).padStart(2, '0');
      time.value = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    };

    // 初始化视频播放器
    const initVideoPlayers = () => {
      cameras.value.forEach((camera, index) => {
        const videoOptions = {
          controls: true,
          autoplay: true,
          preload: 'auto',
          muted: true,
          fluid: true,
          sources: [
            {
              src: camera.url,
              type: 'application/x-mpegURL'
            }
          ]
        };

        const videoElement = document.createElement('video');
        videoElement.className = 'video-js vjs-default-skin';
        const videoContainer = document.getElementById(`video-container-${index}`);
        if (videoContainer) {
          videoContainer.appendChild(videoElement);
          const player = videojs(videoElement, videoOptions);
          players.push(player);
        }
      });
    };

    // 打开标注页面
    const openAnnotation = (camera) => {
      const url = `/annotation?cameraId=${camera.id}&view=${camera.view}`;
      window.open(url, '_blank');
    };

    onMounted(() => {
      updateTime();
      timerId = setInterval(updateTime, 1000);
      
      // 初始化视频播放
      setTimeout(() => {
        initVideoPlayers();
      }, 100);
    });

    onBeforeUnmount(() => {
      if (timerId) clearInterval(timerId);
      
      // 销毁视频播放器
      players.forEach(player => {
        if (player) player.dispose();
      });
    });

    return {
      time,
      yongnianData,
      feixiangData,
      cameras,
      warningData,
      openAnnotation
    };
  }
});
</script>

<style lang="scss" scoped>
// 全屏容器样式
.data-screen-container {
  width: 100%;
  height: 100vh;
  background-color: #040b35;
  background-image: 
    radial-gradient(circle at 30% 30%, rgba(30, 50, 120, 0.3) 0%, rgba(4, 11, 53, 0) 40%),
    radial-gradient(circle at 70% 70%, rgba(30, 50, 120, 0.3) 0%, rgba(4, 11, 53, 0) 40%);
  color: #c0c9d2;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

// 头部样式
.screen-header {
  width: 100%;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  background: linear-gradient(to bottom, rgba(0, 40, 80, 0.6), transparent);

  .header-lf,
  .header-rg {
    width: 300px;
    height: 100%;
    display: flex;
    align-items: center;

    span {
      font-size: 18px;
      color: #c0c9d2;
    }
  }

  .header-ct {
    flex: 1;
    display: flex;
    justify-content: center;

    .header-title {
      position: relative;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;

      .title-text {
        font-size: 36px;
        font-weight: bold;
        background: linear-gradient(to bottom, #fff, #4db6e5);
        -webkit-background-clip: text;
        color: transparent;
        letter-spacing: 4px;
        margin-bottom: 5px;
        z-index: 2;
      }

      .header-title-decoration {
        width: 100%;
        position: relative;
        height: 2px;
        display: flex;
        justify-content: center;

        .line-left, .line-right {
          width: 150px;
          height: 2px;
          background: linear-gradient(to right, transparent, rgba(77, 182, 229, 0.8) 20%, rgba(77, 182, 229, 0.8) 80%, transparent);
          margin: 0 5px;
        }

        &::before, &::after {
          content: '';
          position: absolute;
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background-color: #4db6e5;
          top: -4px;
          transform: translateX(-50%);
          box-shadow: 0 0 10px #4db6e5;
        }

        &::before {
          left: 42%;
        }

        &::after {
          left: 58%;
        }
      }
    }
  }
}

// 内容区域样式
.screen-content {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-gap: 20px;
  padding: 10px 40px 20px;

  .screen-left,
  .screen-center,
  .screen-right {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .progress-panel,
  .center-top,
  .center-bottom {
    height: auto;
    background-color: rgba(6, 30, 93, 0.5);
    border: 1px solid rgba(65, 105, 225, 0.3);
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
    padding: 15px;
  }

  .progress-panel {
    max-height: calc(100vh - 70px);
    position: relative;

    .panel-title {
      font-size: 18px;
      color: #fff;
      margin-bottom: 15px;
      padding-left: 10px;
      border-left: 4px solid #4db6e5;
    }

    .construction-progress {
      height: calc(100% - 35px);
      overflow-y: auto;
      padding-right: 10px;

      /* 滚动条样式 */
      &::-webkit-scrollbar {
        width: 6px;
      }

      &::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 3px;
      }

      &::-webkit-scrollbar-thumb {
        background: rgba(77, 182, 229, 0.5);
        border-radius: 3px;
      }

      &::-webkit-scrollbar-thumb:hover {
        background: rgba(77, 182, 229, 0.7);
      }
    }
  }

  .center-top {
    flex: 3;
  }

  .center-bottom {
    flex: 1;
  }

  .center-title,
  .warning-title {
    font-size: 18px;
    color: #fff;
    margin-bottom: 15px;
    padding-left: 10px;
    border-left: 4px solid #4db6e5;
  }

  // 施工进度样式
  .construction-progress {
    .progress-item {
      margin-bottom: 15px;

      .item-title {
        font-size: 16px;
        margin-bottom: 10px;
        color: #00d0ff;
      }

      .process-list {
        .process-item {
          display: flex;
          align-items: center;
          margin-bottom: 8px;

          .process-name {
            width: 120px;
            font-size: 14px;
          }

          .process-bar {
            flex: 1;
            height: 12px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            margin: 0 10px;
            overflow: hidden;

            .bar-inner {
              height: 100%;
              background: linear-gradient(to right, #4db6e5, #4992ff);
              border-radius: 6px;
            }
          }

          .process-percentage {
            width: 120px;
            font-size: 12px;
            color: #fff;
            text-align: right;
          }
        }
      }
    }
  }

  // 摄像头样式
  .camera-container {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: repeat(2, 1fr);
    grid-gap: 15px;
    height: calc(100% - 30px);

    .camera-item {
      position: relative;
      background-color: rgba(0, 0, 0, 0.2);
      border-radius: 4px;
      overflow: hidden;
      cursor: pointer;

      &:hover {
        box-shadow: 0 0 10px rgba(0, 208, 255, 0.5);
      }

      .camera-title {
        position: absolute;
        top: 10px;
        left: 10px;
        background-color: rgba(0, 0, 0, 0.6);
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 12px;
        color: #fff;
        z-index: 2;
      }

      .video-container {
        width: 100%;
        height: 100%;
      }
    }
  }

  // 预警信息样式
  .warning-container {
    height: 100%;

    .warning-content {
      display: flex;
      justify-content: space-around;
      height: calc(100% - 30px);
      align-items: center;

      .warning-item {
        display: flex;
        align-items: center;
        background-color: rgba(255, 87, 51, 0.2);
        border: 1px solid rgba(255, 87, 51, 0.3);
        border-radius: 8px;
        padding: 15px 15px;

        .warning-icon {
          font-size: 24px;
          color: #ff5733;
          margin-right: 10px;
        }

        .warning-text {
          .warning-type {
            font-size: 16px;
          }

          .warning-count {
            font-size: 20px;
            color: #ff5733;
            font-weight: bold;
          }
        }
      }
    }
  }
}

// 适配不同屏幕大小
@media screen and (max-width: 1600px) {
  .header-title .title-text {
    font-size: 32px;
  }
  .screen-content {
    padding: 5px 30px 20px;
  }
}

@media screen and (max-width: 1400px) {
  .header-title .title-text {
    font-size: 28px;
  }
  .screen-content {
    padding: 5px 20px 20px;
  }
  .construction-progress .progress-item .process-list .process-item .process-name {
    width: 100px;
  }
  .construction-progress .progress-item .process-list .process-item .process-percentage {
    width: 100px;
  }
}
</style>