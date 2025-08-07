<template>
  <div class="dataScreen-container">
    <div class="dataScreen-content" ref="dataScreenRef">
      <div class="dataScreen-header">
        <div class="header-lf">
          <span class="header-screening" @click="router.push('/')">首页</span>
        </div>
        <div class="header-ct">
          <div class="header-ct-title">
            <span>互通施工关键流程的智慧管理平台</span>
          </div>
        </div>
        <div class="header-ri">
          <span class="header-download">录像回放</span>
          <span class="header-time">当前时间：{{ time }}</span>
        </div>
      </div>
      <div class="dataScreen-main">

        <div class="dataScreen-lf">
          <div class="dataScreen-lf-container">
            <div class="dataScreen-main-title">
              <span>工程完成度</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart-container">
              <div class="pie-chart-item" v-for="i in 8" :key="i">
                <AgeRatioChart />
              </div>
            </div>
          </div>
        </div>

        <div class="dataScreen-ct">
          <div class="dataScreen-map">
            <div class="dataScreen-map-title">摄像头实时画面</div>
            <HandanMapChart />
          </div>
          <div class="dataScreen-cb">
              <div class="cb-item">
                <div class="dataScreen-main-title">
                  <span>施工进度查询</span>
                  <img src="./images/dataScreen-title.png" alt="" />
                </div>
                <div class="dataScreen-main-chart">
                  <div class="table-placeholder">施工进度查询 表格</div>
                </div>
              </div>
              <div class="cb-item">
                <div class="dataScreen-main-title">
                  <span>安全事件查询</span>
                  <img src="./images/dataScreen-title.png" alt="" />
                </div>
                <div class="dataScreen-main-chart">
                   <div class="table-placeholder">安全事件查询 表格</div>
                </div>
              </div>
          </div>
        </div>

        <div class="dataScreen-rg">
          <div class="dataScreen-rg-top">
            <div class="dataScreen-main-title">
              <span>安全预警</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart">
              <div class="table-placeholder">安全预警 表格</div>
            </div>
          </div>
          <div class="dataScreen-rg-bottom">
            <div class="dataScreen-main-title">
              <span>施工进度延期预警</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart">
              <div class="table-placeholder">施工进度延期预警 表格</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="dataScreen">
import { ref, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import AgeRatioChart from "./components/AgeRatioChart.vue";
import HandanMapChart from "./components/HandanMapChart.vue";
import dayjs from "dayjs";

const router = useRouter();
const dataScreenRef = ref<HTMLElement | null>(null);

onMounted(() => {
  if (dataScreenRef.value) {
    dataScreenRef.value.style.transform = `scale(${getScale()}) translate(-50%, -50%)`;
    dataScreenRef.value.style.width = `1920px`;
    dataScreenRef.value.style.height = `1080px`;
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
  return ww < wh ? ww : wh;
};

// 获取当前时间
let timer: NodeJS.Timer | null = null;
let time = ref<string>(dayjs().format("YYYY年MM月DD HH:mm:ss"));
timer = setInterval(() => {
  time.value = dayjs().format("YYYY年MM月DD HH:mm:ss");
}, 1000);

onBeforeUnmount(() => {
  window.removeEventListener("resize", resize);
  clearInterval(timer as unknown as number);
});
</script>
<style lang="scss" scoped>
@use "./index.scss";

// Additional styles for placeholders
.table-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  color: #fff;
  font-size: 16px;
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px dashed #05e8fe;
  border-radius: 4px;
  padding: 10px;
  box-sizing: border-box;
}
</style>
