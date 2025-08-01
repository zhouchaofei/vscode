<template>
  <div class="data-screen-container">
    <!-- 1. 背景和带动画效果的头部 -->
    <div class="screen-header">
      <div class="header-lf">
        <span class="header-screening" @click="openVideoPlayback">视频回放</span>
        <span class="header-screening" v-show="false">首页</span>
      </div>
      <div class="header-ct">
        <div class="header-title">
          <span class="title-text">互通施工关键流程的智慧管理平台</span>
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
    // --- EZVIZ API Configuration ---
    const appKey = 'd4baaab8baf24baa9541f1bbe64b2200';
    const appSecret = 'f42fb82edaed28c57b2045d882f0208e';
    
    const time = ref('');
    const warningData = ref({
      helmetMissing: 0,
      unauthorizedEntry: 0
    });

    // 永年北互通数据
    const yongnianData = ref([
      {
        "name": "AK0+851.73A匝道跨线桥",
        "processes": [
            { "name": "预制梁", "completed": 20, "total": 30, "percentage": 67 },
            { "name": "现浇段", "completed": 0, "total": 6, "percentage": 0 },
            { "name": "桥墩", "completed": 29, "total": 35, "percentage": 83 },
            { "name": "盖梁", "completed": 6, "total": 12, "percentage": 50 },
            { "name": "桩", "completed": 43, "total": 43, "percentage": 100 },
            { "name": "护栏", "completed": 0, "total": 330, "percentage": 0 },
            { "name": "水泥桥面铺装", "completed": 0, "total": 330, "percentage": 0 },
            { "name": "沥青桥面铺装", "completed": 0, "total": 330, "percentage": 0 }
        ]
      },
      {
        "name": "A匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 100 },
            { "name": "粉煤灰", "percentage": 40 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
      {
        "name": "B匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 100 },
            { "name": "粉煤灰", "percentage": 0 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
      {
        "name": "C匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 100 },
            { "name": "粉煤灰", "percentage": 0 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
      {
        "name": "D匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 100 },
            { "name": "粉煤灰", "percentage": 30 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
      {
        "name": "E匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 100 },
            { "name": "粉煤灰", "percentage": 25 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
    ]);

    // 肥乡西互通数据
    const feixiangData = ref([
      {
        "name": "A匝道1号跨线桥",
        "processes": [
            { "name": "预制梁", "completed": 2, "total": 30, "percentage": 7 },
            { "name": "桥墩", "completed": 15, "total": 15, "percentage": 100 },
            { "name": "盖梁", "completed": 2, "total": 5, "percentage": 40 },
            { "name": "桩", "completed": 21, "total": 21, "percentage": 100 },
            { "name": "护栏", "completed": 0, "total": 330, "percentage": 0 },
            { "name": "水泥桥面铺装", "completed": 0, "total": 330, "percentage": 0 },
            { "name": "沥青桥面铺装", "completed": 0, "total": 330, "percentage": 0 }
        ]
      },
      {
        "name": "A匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 70 },
            { "name": "粉煤灰", "percentage": 0 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
      {
        "name": "B匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 90 },
            { "name": "粉煤灰", "percentage": 0 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
      {
        "name": "C匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 90 },
            { "name": "粉煤灰", "percentage": 0 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
      {
        "name": "D匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 90 },
            { "name": "粉煤灰", "percentage": 0 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
      {
        "name": "E匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 80 },
            { "name": "粉煤灰", "percentage": 0 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
      {
        "name": "F匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 90 },
            { "name": "粉煤灰", "percentage": 0 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
      {
        "name": "G匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 90 },
            { "name": "粉煤灰", "percentage": 0 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
      {
        "name": "H匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 70 },
            { "name": "粉煤灰", "percentage": 0 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      },
      {
        "name": "I匝道",
        "processes": [
            { "name": "挖台阶", "percentage": 60 },
            { "name": "粉煤灰", "percentage": 0 },
            { "name": "水泥稳定碎石", "percentage": 0 },
            { "name": "沥青砼底面层", "percentage": 0 },
            { "name": "沥青砼表面层", "percentage": 0 }
        ]
      }
    ]);

    // 摄像头数据
    // --- MODIFIED: Camera data now includes deviceSerial and an empty URL ---
    const cameras = ref([
      { id: 1, name: '永年', english: 'yn', deviceSerial: '33011063992677425735:33010516991327760034', url: '', view: 'view1' },
      { id: 2, name: '肥乡北', english: 'fx_n', deviceSerial: '33011063992677425735:33010084991327588111', url: '', view: 'view1' },
      { id: 3, name: '肥乡南', english: 'fx_s', deviceSerial: '33011063992677425735:33011012991327147072', url: '', view: 'view1' },
      { id: 4, name: '肥乡梁厂', english: 'fx_lc', deviceSerial: '33011063992677425735:33011033991327056374', url: '', view: 'view1' }
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

    // --- NEW: Function to get a valid accessToken ---
    const getValidAccessToken = async () => {
      const tokenInfo = JSON.parse(localStorage.getItem('ys7TokenInfo'));

      // Check if a valid, unexpired token exists
      if (tokenInfo && tokenInfo.accessToken && tokenInfo.expireTime > Date.now()) {
        console.log("Using cached accessToken.");
        return tokenInfo.accessToken;
      }
      
      console.log("正在获取新的 accessToken...");
      const url = 'https://open.ys7.com/api/lapp/token/get';
      const params = new URLSearchParams();
      params.append('appKey', appKey);
      params.append('appSecret', appSecret);

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: params
        });
        
        const data = await response.json();

        if (data.code === '200') {
          const { accessToken, expireTime } = data.data;
          // Store the new token and its expiry time
          localStorage.setItem('ys7TokenInfo', JSON.stringify({ accessToken, expireTime }));
          console.log("成功获取并存储新的 accessToken");
          return accessToken;
        } else {
          // Handle API error
          console.error(`Error fetching accessToken: ${data.msg} (Code: ${data.code})`);
          throw new Error(`API Error: ${data.msg}`);
        }
      } catch (error) {
        console.error("Network or fetch error while getting accessToken:", error);
        throw error;
      }
    };
    
    // --- NEW: Function to fetch all camera URLs ---
    const fetchAllCameraUrls = async (token) => {
      console.log("正在获取摄像头 URLs...");
      const url = 'https://open.ys7.com/api/lapp/v2/live/address/get';
      
      const promises = cameras.value.map(async (camera) => {
        const params = new URLSearchParams();
        params.append('accessToken', token);
        params.append('deviceSerial', camera.deviceSerial);
        params.append('channelNo', 1);
        params.append('protocol', 2);

        try {
          const response = await fetch(url, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: params
          });
          const data = await response.json();
          if (data.code === '200' && data.data) {
            // Update the camera's URL
            camera.url = data.data.url;
            console.log(`URL for ${camera.name} updated.`);
          } else {
             console.error(`Failed to get URL for ${camera.name}: ${data.msg} (Code: ${data.code})`);
          }
        } catch(error) {
           console.error(`Network error while fetching URL for ${camera.name}:`, error);
        }
      });
      
      // Wait for all requests to complete
      await Promise.all(promises);
      console.log("All camera URL fetch requests completed.");
    };

    // 初始化视频播放器
    const initVideoPlayers = () => {
      cameras.value.forEach((camera, index) => {
        // Only initialize if a URL was successfully fetched
        if (!camera.url) {
            console.warn(`Skipping video player for ${camera.name} as URL is missing.`);
            return;
        }

        const videoOptions = {
          // controls: true,
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
          videoContainer.innerHTML = ''; // Clear previous player if any
          videoContainer.appendChild(videoElement);
          const player = videojs(videoElement, videoOptions);
          players.push(player);
        }
      });
    };

    // 打开标注页面
    // --- MODIFIED: Pass accessToken and cameraName to annotation page ---
    const openAnnotation = (camera) => {
        const tokenInfo = JSON.parse(localStorage.getItem('ys7TokenInfo'));
        if (!tokenInfo || !tokenInfo.accessToken) {
            alert("Access Token not available. Please refresh the page.");
            return;
        }

        // Pass the token and identifiers. Annotation.vue will fetch its own URLs.
        const url = `/annotation?accessToken=${tokenInfo.accessToken}&cameraName=${encodeURIComponent(camera.english)}&view=${camera.view}`;
        window.open(url, '_blank');
    };

    // 打开视频回放页面
    const openVideoPlayback = () => {
      const url = `/videoplayback`;
      window.open(url, '_blank');
    };

    // --- MODIFIED: Updated onMounted lifecycle hook ---
    onMounted(async () => {
      updateTime();
      timerId = setInterval(updateTime, 1000);
      
      try {
        // 1. Get a valid token
        const accessToken = await getValidAccessToken();
        
        // 2. Fetch all camera URLs using the token
        await fetchAllCameraUrls(accessToken);
        
        // 3. Initialize video players with the new URLs
        // Use a timeout to ensure the DOM is ready
        setTimeout(() => {
            initVideoPlayers();
        }, 100);

      } catch (error) {
        alert("Failed to initialize camera streams. Please check the console for details.");
      }
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
      openAnnotation,
      openVideoPlayback
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

  .header-lf {
    .header-screening {
      cursor: pointer;
      margin-right: 20px;
      &:hover {
        color: #fff;
      }
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