<template>
  <div class="dataScreen-container">
    <div class="dataScreen-content" ref="dataScreenRef">
      <div class="dataScreen-header">
        <div class="header-lf">
          <span class="header-screening">首页</span>
        </div>
        <div class="header-ct">
          <div class="header-ct-title">
            <span>智慧旅游可视化大数据展示平台</span>
            <div class="header-ct-warning">平台高峰预警信息（2条）</div>
          </div>
        </div>
        <div class="header-ri">
          <span class="header-download">统计报告</span>
          <span class="header-time">当前时间：{{ time }}</span>
        </div>
      </div>
      <div class="dataScreen-main">
        <div class="dataScreen-lf">
          <div class="dataScreen-top">
            <div class="dataScreen-main-title">
              <span>实时游客统计</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart">
              <RealTimeAccessChart />
            </div>
          </div>
          <div class="dataScreen-center">
            <div class="dataScreen-main-title">
              <span>男女比例</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart">
              <MaleFemaleRatioChart />
            </div>
          </div>
          <div class="dataScreen-bottom">
            <div class="dataScreen-main-title">
              <span>年龄比例</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart">
              <AgeRatioChart />
            </div>
          </div>
        </div>
        <div class="dataScreen-ct">
          <div class="dataScreen-map">
            <div class="dataScreen-map-title">景区实时客流量</div>
            <!-- <vue3-seamless-scroll
							:list="alarmData"
							class="dataScreen-alarm"
							:step="0.5"
							:hover="true"
							:limitScrollNum="3"
						>
							<div class="dataScreen-alarm">
								<div class="map-item" v-for="item in alarmData" :key="item.id">
									<img src="./images/dataScreen-alarm.png" alt="" />
									<span class="map-alarm sle">{{ item.label }} 预警：{{ item.warnMsg }}</span>
								</div>
							</div>
						</vue3-seamless-scroll> -->
            <ChinaMapChart />
          </div>
          <div class="dataScreen-cb">
            <div class="dataScreen-main-title">
              <span>未来30天游客量趋势图</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart">
              <OverNext30Chart />
            </div>
          </div>
        </div>
        <div class="dataScreen-rg">
          <div class="dataScreen-top">
            <div class="dataScreen-main-title">
              <span>热门景区排行</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart">
              <HotPlateChart />
            </div>
          </div>
          <div class="dataScreen-center">
            <div class="dataScreen-main-title">
              <span>年度游客量对比</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart">
              <AnnualUseChart />
            </div>
          </div>
          <div class="dataScreen-bottom">
            <div class="dataScreen-main-title">
              <span>预约渠道数据统计</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart">
              <PlatformSourceChart />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup name="dataScreen">
import { ref, onMounted, onBeforeUnmount } from "vue";
import { HOME_URL } from "../../config/index.js";
import AgeRatioChart from "./components/SimpleAgeRatioChart.vue";
import AnnualUseChart from "./components/SimpleAnnualUseChart.vue";
import ChinaMapChart from "./components/SimpleChinaMapChart.vue";
import HotPlateChart from "./components/SimpleHotPlateChart.vue";
import MaleFemaleRatioChart from "./components/SimpleMaleFemaleRatioChart.vue";
import OverNext30Chart from "./components/SimpleOverNext30Chart.vue";
import PlatformSourceChart from "./components/SimplePlatformSourceChart.vue";
import RealTimeAccessChart from "./components/SimpleRealTimeAccessChart.vue";
import dayjs from "dayjs";

// Remove router functionality for now since we're not using router
const dataScreenRef = ref(null);

onMounted(() => {
  // Simplified approach - just set basic dimensions for now
  if (dataScreenRef.value) {
    dataScreenRef.value.style.width = `100%`;
    dataScreenRef.value.style.height = `100%`;
  }
  window.addEventListener("resize", resize);
});

// 设置响应式
const resize = () => {
  if (dataScreenRef.value) {
    dataScreenRef.value.style.transform = `scale(${getScale()}) translate(-50%, -50%)`;
  }
};

// 根据浏览器大小推断缩放比例
const getScale = (width = 1920, height = 1080) => {
  let ww = window.innerWidth / width;
  let wh = window.innerHeight / height;
  return Math.min(ww, wh);
};

// 获取当前时间
let timer = null;
let time = ref(dayjs().format("YYYY年MM月DD HH:mm:ss"));
timer = setInterval(() => {
  time.value = dayjs().format("YYYY年MM月DD HH:mm:ss");
}, 1000);

onBeforeUnmount(() => {
  window.removeEventListener("resize", resize);
  clearInterval(timer);
});
</script>
<style lang="scss" scoped>
.dataScreen-container {
  width: 100%;
  height: 100vh;
  background: url("./images/bg.png") no-repeat;
  background-size: cover;
  background-position: center;
  position: relative;
  
  .dataScreen-content {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    transform-origin: left top;
    
    .dataScreen-header {
      display: flex;
      width: 100%;
      height: 80px;
      position: relative;
      
      .header-lf,
      .header-ri {
        position: relative;
        width: 400px;
        height: 100%;
        background: url("./images/dataScreen-header-left-bg.png") no-repeat;
        background-size: 100% 100%;
        display: flex;
        align-items: center;
        padding: 0 20px;
      }
      
      .header-ri {
        background: url("./images/dataScreen-header-right-bg.png") no-repeat;
        background-size: 100% 100%;
        justify-content: flex-end;
      }
      
      .header-ct {
        position: relative;
        flex: 1;
        height: 100%;
        
        .header-ct-title {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          font-size: 24px;
          line-height: 80px;
          color: #05e8fe;
          text-align: center;
          letter-spacing: 2px;
          background: url("./images/dataScreen-header-center-bg.png") no-repeat;
          background-size: 100% 100%;
          
          .header-ct-warning {
            position: absolute;
            bottom: -5px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 12px;
            color: #ff6b6b;
            background: url("./images/dataScreen-header-warn-bg.png") no-repeat;
            background-size: 100% 100%;
            padding: 2px 10px;
          }
        }
      }
      
      .header-screening,
      .header-download {
        color: #ffffff;
        cursor: pointer;
        font-size: 14px;
      }
      
      .header-time {
        color: #ffffff;
        font-size: 14px;
      }
    }
    
    .dataScreen-main {
      display: flex;
      flex: 1;
      padding: 20px;
      gap: 20px;
      
      .dataScreen-lf,
      .dataScreen-rg {
        display: flex;
        flex-direction: column;
        width: 350px;
        gap: 20px;
        
        .dataScreen-top,
        .dataScreen-center,
        .dataScreen-bottom {
          background: url("./images/dataScreen-main-lt.png") no-repeat;
          background-size: 100% 100%;
          border-radius: 8px;
          padding: 15px;
          min-height: 200px;
          
          .dataScreen-main-title {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            
            span {
              color: #ffffff;
              font-size: 16px;
              margin-right: 10px;
            }
            
            img {
              width: 20px;
              height: 20px;
            }
          }
          
          .dataScreen-main-chart {
            height: calc(100% - 40px);
          }
        }
      }
      
      .dataScreen-ct {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 20px;
        
        .dataScreen-map {
          flex: 1;
          background: url("./images/dataScreen-main-cb.png") no-repeat;
          background-size: 100% 100%;
          border-radius: 8px;
          padding: 15px;
          position: relative;
          
          .dataScreen-map-title {
            color: #ffffff;
            font-size: 18px;
            text-align: center;
            margin-bottom: 15px;
          }
        }
        
        .dataScreen-cb {
          height: 300px;
          background: url("./images/dataScreen-main-cb.png") no-repeat;
          background-size: 100% 100%;
          border-radius: 8px;
          padding: 15px;
          
          .dataScreen-main-title {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            
            span {
              color: #ffffff;
              font-size: 16px;
              margin-right: 10px;
            }
            
            img {
              width: 20px;
              height: 20px;
            }
          }
          
          .dataScreen-main-chart {
            height: calc(100% - 40px);
          }
        }
      }
    }
  }
}
</style>
