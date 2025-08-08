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
          <span class="header-download" @click="openVideoPlayback">录像回放</span>
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
              <div class="cb-header">
                <div class="dataScreen-main-title">
                  <span>施工进度查询</span>
                  <img src="./images/dataScreen-title.png" alt="" />
                </div>
                <div class="filters">
                  <select v-model="progressFilters.location">
                    <option v-for="loc in progressLocations" :key="loc" :value="loc">{{ loc }}</option>
                  </select>
                  <select v-model="progressFilters.structure">
                    <option v-for="struc in progressStructures" :key="struc" :value="struc">{{ struc }}</option>
                  </select>
                  <select v-model="progressFilters.model">
                    <option v-for="mod in progressModels" :key="mod" :value="mod">{{ mod }}</option>
                  </select>
                </div>
              </div>
              <div class="dataScreen-main-chart">
                <div class="custom-table-container">
                  <table class="custom-table">
                    <thead>
                      <tr>
                        <th>工序</th>
                        <th>开始时间</th>
                        <th>结束时间</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(item, index) in progressData" :key="index">
                        <td>{{ item.state }}</td>
                        <td>{{ item.start_date }}</td>
                        <td>{{ item.end_date }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
            <div class="cb-item">
              <div class="cb-header">
                <div class="dataScreen-main-title">
                  <span>安全事件查询</span>
                  <img src="./images/dataScreen-title.png" alt="" />
                </div>
                <div class="filters">
                  <select v-model="safetyEventFilter">
                    <option>永年</option>
                    <option>肥乡北</option>
                    <option>肥乡南</option>
                    <option>肥乡梁厂</option>
                  </select>
                </div>
              </div>
              <div class="dataScreen-main-chart">
                <div class="custom-table-container">
                  <table class="custom-table">
                    <thead>
                      <tr>
                        <th>事件</th>
                        <th>时间</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(item, index) in safetyEvents" :key="index">
                        <td>{{ item.event }}</td>
                        <td>{{ item.time }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="dataScreen-rg">
          <div class="dataScreen-rg-top">
            <div class="dataScreen-main-title">
              <span>安全事件预警</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart">
              <div class="custom-table-container table-20-rows">
                <table class="custom-table">
                  <thead>
                    <tr>
                      <th>事件</th>
                      <th>地点</th>
                      <th>时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in safetyWarnings" :key="index">
                      <td>{{ item.event }}</td>
                      <td>{{ item.location }}</td>
                      <td>{{ item.time }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div class="dataScreen-rg-bottom">
            <div class="dataScreen-main-title">
              <span>施工进度超期</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart">
              <div class="custom-table-container table-6-rows">
                <table class="custom-table">
                  <thead>
                    <tr>
                      <th>地点</th>
                      <th>事件</th>
                      <th>计划日期</th>
                      <th>延期时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in delayWarnings" :key="index">
                      <td>{{ item.location }}</td>
                      <td>{{ item.event }}</td>
                      <td>{{ item.plannedDate }}</td>
                      <td>{{ item.delayTime }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="dataScreen">
import { ref, onMounted, onBeforeUnmount, watch, computed } from "vue";
import { useRouter } from "vue-router";
import AgeRatioChart from "./components/AgeRatioChart.vue";
import HandanMapChart from "./components/HandanMapChart.vue";
import dayjs from "dayjs";

const router = useRouter();
const dataScreenRef = ref<HTMLElement | null>(null);

// 1. Added function to handle video playback button click
const openVideoPlayback = () => {
  const url = `/videoplayback`;
  window.open(url, '_blank');
};

// ======================= 添加工程完成度数据获取逻辑 =======================

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
    const response = await fetch(`http://59.110.65.210:8081/data?location=${selectedLocation.value}`);
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

// ======================= Table and Filter Data =======================
// 2. Updated mock data for the construction progress table
const progressData = ref([
    { "state": "开挖台阶", "start_date": "2025-07-12", "end_date": "2025-07-20" },
    { "state": "浇筑垫层", "start_date": "2025-07-21", "end_date": "2025-07-22" },
    { "state": "钢筋绑扎", "start_date": "2025-07-23", "end_date": "2025-08-01" },
    { "state": "模板安装", "start_date": "2025-08-02", "end_date": "2025-08-05" },
    { "state": "混凝土浇筑", "start_date": "2025-08-06", "end_date": "" },
    { "state": "养护", "start_date": "", "end_date": "" },
]);
const safetyEvents = ref(Array.from({ length: 4 }, (_, i) => ({ event: `违规操作 ${i + 1}`, time: `2025-08-0${(i % 3) + 1}` })));
const safetyWarnings = ref(Array.from({ length: 25 }, (_, i) => ({ event: `设备离线 ${i + 1}`, location: '永年', time: `2025-08-0${(i % 4) + 1}` })));
const delayWarnings = ref(Array.from({ length: 7 }, (_, i) => ({ location: '肥乡北', event: `桥墩 ${i + 1}# 延期`, plannedDate: '2025-09-10', delayTime: `${i + 1}天` })));

const safetyEventFilter = ref('肥乡梁厂');

const progressFilterOptions = {
  '永年': {
    '桥台': ['0#Z-1', '0#Z-2', '0#Z-3', '11#Z-1', '11#Z-2', '11#Z-3'],
    '桥墩': ['1#Z-1', '1#Z-2', '1#Z-3', '2#Z-1', '2#Z-2', '2#Z-3', '3#Z-1', '3#Z-2', '3#Z-3', '4#Z-1', '4#Z-2', '4#Z-3', '5#Z-1', '5#Z-2', '5#Z-3', '6#Z-1', '6#Z-2', '6#Z-3', '7#Z-1', '7#Z-2', '7#Z-3', '8#Z-1', '8#Z-2', '8#Z-3', '9#Z-1', '9#Z-2', '9#Z-3', '10#Z-1', '10#Z-2'],
    '盖梁': ['0#', '1#', '2#', '3#', '4#', '5#', '6#', '7#', '8#', '9#', '10#', '11#'],
    '预制箱梁': ['XL1-1', 'XL1-2', 'XL1-3', 'XL1-4', 'XL1-5', 'XL2-1', 'XL2-2', 'XL2-3', 'XL2-4', 'XL2-5', 'XL3-1', 'XL3-2', 'XL3-3', 'XL3-4', 'XL3-5', 'XL4-1', 'XL4-2', 'XL4-3', 'XL4-4', 'XL4-5', 'XL5-1', 'XL5-2', 'XL5-3', 'XL5-4', 'XL5-5', 'XL6-1', 'XL6-2', 'XL6-3', 'XL6-4', 'XL6-5'],
    '现浇箱梁': ['XL7', 'XL8', 'XL9', 'XL10', 'XL11'],
    '护栏': ['HL'],
    '横向湿接缝': ['SJFH'],
    '纵向湿接缝': ['SJFZ'],
    '匝道': ['A', 'B', 'C', 'D', 'E'],
    '通道': ['CK0+192.289', 'EK0+185.5', 'K410+077.744', 'K410+427.139'],
    '涵洞': ['CK0+310', 'DK0+280', 'GK0+432']
  },
  '肥乡北': {
    '桥台': ['0#Z-1', '0#Z-2', '0#Z-3', '4#Z-1', '4#Z-2', '4#Z-3'],
    '桥墩': ['1#Z-1', '1#Z-2', '1#Z-3', '2#Z-1', '2#Z-2', '2#Z-3', '3#Z-1', '3#Z-2', '3#Z-3'],
    '盖梁': ['0#', '1#', '2#', '3#', '4#'],
    '预制箱梁': ['XL1-1', 'XL1-2', 'XL1-3', 'XL1-4', 'XL1-5', 'XL2-1', 'XL2-2', 'XL2-3', 'XL2-4', 'XL2-5', 'XL3-1', 'XL3-2', 'XL3-3', 'XL3-4', 'XL3-5', 'XL4-1', 'XL4-2', 'XL4-3', 'XL4-4', 'XL4-5'],
    '护栏': ['HL'],
    '横向湿接缝': ['SJFH'],
    '纵向湿接缝': ['SJFZ'],
    '匝道': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'],
    '通道': ['K47+731.832', 'AK0+800'],
    '涵洞': ['BK0+370', 'CK0+080', 'DK0+310', 'EK0+270', 'FK0+070', 'GK0+240', 'HK0+300', 'IK0+160'],
    '路肩墙': ['AK0+000-AK0+080']
  },
  '肥乡南': {
    '桥台': ['0#Z-1', '0#Z-2', '0#Z-3', '5#Z-1', '5#Z-2', '5#Z-3'],
    '桥墩': ['1#Z-1', '1#Z-2', '1#Z-3', '2#Z-1', '2#Z-2', '2#Z-3', '3#Z-1', '3#Z-2', '3#Z-3', '4#Z-1', '4#Z-2', '4#Z-3'],
    '盖梁': ['0#', '1#', '2#', '3#', '4#', '5#'],
    '预制箱梁': ['XL1-1', 'XL1-2', 'XL1-3', 'XL1-4', 'XL1-5', 'XL2-1', 'XL2-2', 'XL2-3', 'XL2-4', 'XL2-5', 'XL3-1', 'XL3-2', 'XL3-3', 'XL3-4', 'XL3-5', 'XL4-1', 'XL4-2', 'XL4-3', 'XL4-4', 'XL4-5', 'XL5-1', 'XL5-2', 'XL5-3', 'XL5-4', 'XL5-5'],
    '护栏': ['HL'],
    '横向湿接缝': ['SJFH'],
    '纵向湿接缝': ['SJFZ'],
    '匝道': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'],
    '通道': ['K47+731.832', 'AK0+800'],
    '涵洞': ['BK0+370', 'CK0+080', 'DK0+310', 'EK0+270', 'FK0+070', 'GK0+240', 'HK0+300', 'IK0+160'],
    '路肩墙': ['AK0+830-AK0+869.718']
  }
};

const progressFilters = ref({
  location: '永年',
  structure: '匝道',
  model: 'A'
});

const progressLocations = computed(() => Object.keys(progressFilterOptions));
const progressStructures = computed(() => {
  const loc = progressFilters.value.location as keyof typeof progressFilterOptions;
  return Object.keys(progressFilterOptions[loc]);
});
const progressModels = computed(() => {
  const loc = progressFilters.value.location as keyof typeof progressFilterOptions;
  const struc = progressFilters.value.structure as keyof typeof progressFilterOptions[typeof loc];
  return progressFilterOptions[loc][struc] || [];
});

watch(() => progressFilters.value.location, (newLocation) => {
  const newStructures = Object.keys(progressFilterOptions[newLocation as keyof typeof progressFilterOptions]);
  progressFilters.value.structure = newStructures[0];
});

watch(() => progressFilters.value.structure, (newStructure) => {
  const loc = progressFilters.value.location as keyof typeof progressFilterOptions;
  const newModels = progressFilterOptions[loc][newStructure as keyof typeof progressFilterOptions[typeof loc]] || [];
  progressFilters.value.model = newModels[0];
});


// ===================================================================

onMounted(() => {
  // 页面加载时获取默认数据
  fetchData();
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

// ======================= 筛选框样式 =======================
.lf-header {
  // position: absolute;
  // top: 0;
  // left: 0;
  // right: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  // padding-right: 20px;
  padding: 0 30px 0 0; // 增加右边距
  // height: 40px; // Explicit height
}

.location-filter select,
.filters select {
  background-color: rgba(0, 0, 0, 0.3);
  color: #fff;
  border: 1px solid #05e8fe;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 16px;
  outline: none;
  cursor: pointer;
  transition: all 0.3s ease; // 添加过渡
  margin-left: 10px;
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

.location-filter select:hover,
.filters select:hover {
  border-color: #fff;
  box-shadow: 0 0 10px rgba(5, 232, 254, 0.5);
}

.location-filter option,
.filters option {
  background-color: #0d2a42;
  color: #fff;
}

// .dataScreen-main-title {
//   position: static; /* 覆盖原来的 absolute 定位 */
// }

.loading-text {
  color: #fff;
  width: 100%;
  text-align: center;
  margin-top: 50px;
}
// ==========================================================

// Table styles
.custom-table-container {
  height: 100%;
  overflow-y: auto;
  
  &.table-20-rows {
    // 20 rows * 30px/row + 30px header
    max-height: calc(20 * 30px + 30px);
  }

  &.table-6-rows {
    max-height: calc(6 * 30px + 30px);
  }
}

.custom-table {
  width: 100%;
  border-collapse: collapse;
  color: #fff;
  font-size: 16px;
  
  thead tr {
    // background-color: rgba(5, 232, 254, 0.2);
    background-color: transparent; // Ensure background is not semi-transparent
    position: sticky;
    top: 0;
    z-index: 1;
  }
  
  th {
    background: #0d2a42; // Solid background for header cells
    padding: 8px;
    text-align: center;
    border-bottom: 1px solid rgba(5, 232, 254, 0.1);
  }

  td {
    padding: 8px;
    text-align: center;
    border-bottom: 1px solid rgba(5, 232, 254, 0.1);
  }
  
  tbody tr:nth-child(odd) {
    background-color: rgba(255, 255, 255, 0.05);
  }
  
  tbody tr:nth-child(even) {
    background-color: rgba(0, 0, 0, 0.1);
  }
  
  tbody tr:hover {
    background-color: rgba(5, 232, 254, 0.3);
  }
}

/* Custom Scrollbar */
.custom-table-container::-webkit-scrollbar {
  width: 8px;
}
.custom-table-container::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}
.custom-table-container::-webkit-scrollbar-thumb {
  background: rgba(5, 232, 254, 0.5);
  border-radius: 4px;
}
.custom-table-container::-webkit-scrollbar-thumb:hover {
  background: rgba(5, 232, 254, 0.8);
}

.cb-header {
  // position: absolute;
  // top: 1px;
  // left: 0;
  // right: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 10px 0 0;
  // padding: 0 10px;
  // height: 45px; // Explicit height
}

.filters {
  display: flex;
  gap: 5px;
}

</style>
