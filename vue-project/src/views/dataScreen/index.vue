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
            <div class="lf-header">
              <div class="dataScreen-main-title">
                <span>工程完成度</span>
                <img src="./images/dataScreen-title.png" alt="" />
              </div>
              <div class="location-filter">
                <select v-model="selectedLocation">
                  <option value="yn">永年</option>
                  <option value="fx_n">肥乡北</option>
                  <option value="fx_s">肥乡南</option>
                </select>
              </div>
            </div>
            <div class="dataScreen-main-chart-container">
              <div v-if="loading" class="loading-text">加载中...</div>
              <div v-else class="pie-chart-item" v-for="item in constructionData" :key="item.cons">
                <AgeRatioChart :chartData="item" />
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
import { ref, onMounted, onBeforeUnmount, watch } from "vue";
import { useRouter } from "vue-router";
import AgeRatioChart from "./components/AgeRatioChart.vue";
import HandanMapChart from "./components/HandanMapChart.vue";
import dayjs from "dayjs";

const router = useRouter();
const dataScreenRef = ref<HTMLElement | null>(null);

// ======================= 2. 添加数据获取逻辑 =======================

// 用于存储图表数据的响应式变量，初始为空数组
const constructionData = ref<any[]>([]);
// 默认选中的地点
const selectedLocation = ref('yn');
// 加载状态
const loading = ref(false);

// 定义获取数据的函数
const fetchData = async () => {
  loading.value = true;
  constructionData.value = []; // 清空旧数据
  try {
    const response = await fetch(`http://10.1.40.6:6000/data?location=${selectedLocation.value}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    constructionData.value = data;
  } catch (error) {
    console.error("获取数据失败:", error);
    // 在这里可以添加一些用户友好的错误提示
  } finally {
    loading.value = false;
  }
};

// 监听 selectedLocation 的变化，并在变化时重新获取数据
watch(selectedLocation, () => {
  fetchData();
});
// ========================================================

const jsonData = [
    {
        "location": "yn",
        "cons": "Z",
        "start_date_plan": "2025-05-01",
        "end_date_plan": "2025-06-08",
        "current_date": "2025-08-06",
        "duration_cons": "97",
        "duration_plan": "39",
        "duration_percent": "248%",
        "total_count": "35",
        "state_count": "29",
        "complete_percent": "82%",
        "un_complete_percent": "18%",
        "countOfUnfinished": "6"
    },
    {
        "location": "yn",
        "cons": "GL",
        "start_date_plan": "2025-05-15",
        "end_date_plan": "2025-08-11",
        "current_date": "2025-08-06",
        "duration_cons": "83",
        "duration_plan": "89",
        "duration_percent": "93%",
        "total_count": "12",
        "state_count": "7",
        "complete_percent": "58%",
        "un_complete_percent": "42%",
        "countOfUnfinished": "5"
    },
    {
        "location": "yn",
        "cons": "YZL_5",
        "start_date_plan": "2025-05-05",
        "end_date_plan": "2025-06-17",
        "current_date": "2025-08-06",
        "duration_cons": "93",
        "duration_plan": "44",
        "duration_percent": "211%",
        "total_count": "35",
        "state_count": "21",
        "complete_percent": "60%",
        "un_complete_percent": "40%",
        "countOfUnfinished": "14"
    },
    {
        "location": "yn",
        "cons": "YZL_6",
        "start_date_plan": "2025-06-19",
        "end_date_plan": "2025-08-26",
        "current_date": "2025-08-06",
        "duration_cons": "48",
        "duration_plan": "69",
        "duration_percent": "69%",
        "total_count": "35",
        "state_count": "0",
        "complete_percent": "0%",
        "un_complete_percent": "100%",
        "countOfUnfinished": "35"
    },
    {
        "location": "yn",
        "cons": "ZD_1",
        "start_date_plan": "2025-05-05",
        "end_date_plan": "2025-08-31",
        "current_date": "2025-08-06",
        "duration_cons": "93",
        "duration_plan": "119",
        "duration_percent": "78%",
        "total_count": "5",
        "state_count": "5",
        "complete_percent": "100%",
        "un_complete_percent": "0%",
        "countOfUnfinished": "0"
    },
    {
        "location": "yn",
        "cons": "ZD_4",
        "start_date_plan": "2025-10-07",
        "end_date_plan": "2025-11-28",
        "current_date": "2025-08-06",
        "duration_cons": "-62",
        "duration_plan": "71",
        "duration_percent": "-87%",
        "total_count": "5",
        "state_count": "0",
        "complete_percent": "0%",
        "un_complete_percent": "100%",
        "countOfUnfinished": "5"
    },
    {
        "location": "yn",
        "cons": "TD",
        "start_date_plan": "2025-04-05",
        "end_date_plan": "2025-08-11",
        "current_date": "2025-08-06",
        "duration_cons": "123",
        "duration_plan": "129",
        "duration_percent": "95%",
        "total_count": "4",
        "state_count": "4",
        "complete_percent": "100%",
        "un_complete_percent": "0%",
        "countOfUnfinished": "0"
    },
    {
        "location": "yn",
        "cons": "HD",
        "start_date_plan": "2025-04-05",
        "end_date_plan": "2025-08-11",
        "current_date": "2025-08-06",
        "duration_cons": "123",
        "duration_plan": "129",
        "duration_percent": "95%",
        "total_count": "3",
        "state_count": "2",
        "complete_percent": "66%",
        "un_complete_percent": "34%",
        "countOfUnfinished": "1"
    }
];
// 将 JSON 数据存到一个响应式引用中
constructionData.value = jsonData

onMounted(() => {
  // 页面加载时获取默认数据
  // fetchData();
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

// ======================= 3. 添加筛选框样式 =======================
.lf-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  // padding-right: 20px;
  padding: 0 30px; // 增加右边距
}

.location-filter select {
  background-color: rgba(0, 0, 0, 0.3);
  color: #fff;
  border: 1px solid #05e8fe;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 18px;
  outline: none;
  cursor: pointer;
  transition: all 0.3s ease; // 添加过渡
}
// .location-filter select {
//   background-color: rgba(0, 0, 0, 0.5); // 背景更深
//   color: #e0e0e0; // 柔和字体色
//   border: 1px solid #05e8fe;
//   border-radius: 5px; // 更圆角
//   padding: 6px 12px; // 更大内边距
//   font-size: 16px; // 更大字体
//   outline: none;
//   cursor: pointer;
//   transition: all 0.3s ease; // 添加过渡
// }

.location-filter select:hover {
  border-color: #fff;
  box-shadow: 0 0 10px rgba(5, 232, 254, 0.5);
}

.location-filter option {
  background-color: #0d2a42;
  color: #fff;
}

.dataScreen-main-title {
  position: static; /* 覆盖原来的 absolute 定位 */
}

.loading-text {
  color: #fff;
  width: 100%;
  text-align: center;
  margin-top: 50px;
}
// ==========================================================

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
