<template>
  <div class="dataScreen-container">
    <div class="dataScreen-content" ref="dataScreenRef">
      <div class="dataScreen-header">
        <div class="header-lf" v-if="allDataLoaded">
          <span class="header-screening" @click="router.push('/')">首页</span>
        </div>
        <div class="header-ct" v-if="allDataLoaded">
          <div class="header-ct-title">
            <span>互通施工关键流程的智慧管理平台</span>
          </div>
        </div>
        <div class="header-ri" v-if="allDataLoaded">
          <span class="header-download" @click="openVideoPlayback">录像回放</span>
          <span class="header-time">当前时间：{{ time }}</span>
        </div>
      </div>
      <div class="dataScreen-main">
        <div class="dataScreen-lf" v-if="allDataLoaded">
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
                <ProjectCompletionChart :chartData="item" />
              </div>
            </div>
          </div>
        </div>
        <div class="loading-container" v-else>
          <div class="loading-spinner"></div>
          <div class="loading-text">数据加载中...</div>
        </div>

        <div class="dataScreen-ct" v-if="allDataLoaded">
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
                        <th>施工地区</th>
                        <th>施工构件</th>
                        <th>施工工序</th>
                        <th>开始时间</th>
                        <th>结束时间</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(item, index) in progressData" :key="index">
                        <td>{{ item.location }}</td>
                        <td>{{ item.structure }}</td>
                        <td>{{ item.state }}</td>
                        <td>{{ item.start_date }}</td>
                        <td>{{ item.end_date }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="dataScreen-rg" v-if="allDataLoaded">
          <div class="dataScreen-rg-top">
            <div class="dataScreen-main-title">
              <span>安全事件预警</span>
              <img src="./images/dataScreen-title.png" alt="" />
            </div>
            <div class="dataScreen-main-chart">
              <div class="custom-table-container table-20-rows">
                <table class="custom-table">
                  <colgroup>
                    <col style="width: 45%;">
                    <col style="width: 22%;">
                    <col style="width: 33%;">
                  </colgroup>
                  <thead>
                    <tr>
                      <th>安全事件</th>
                      <th>地点</th>
                      <th>时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in safetyWarnings" :key="index">
                      <td>{{ item.alert_event }}</td>
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
                      <th>施工区域</th>
                      <th>施工构件</th>
                      <th>计划完成日期</th>
                      <th>延期时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in delayWarnings" :key="index">
                      <td>{{ item.location }}</td>
                      <td>{{ item.cons }}</td>
                      <td>{{ item.end_date_plan }}</td>
                      <td>{{ item.delay_days }}</td>
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
import ProjectCompletionChart from "./components/ProjectCompletionChart.vue";
import HandanMapChart from "./components/HandanMapChart.vue";
import dayjs from "dayjs";

// 总加载状态
const allDataLoaded = ref(false); 

const router = useRouter();
const dataScreenRef = ref<HTMLElement | null>(null);

const openVideoPlayback = () => {
  const url = `/videoplayback`;
  window.open(url, '_blank');
};

// 存储图表数据
const constructionData = ref<any[]>([]);

const selectedLocation = ref('yn');
const loading = ref(false);

const fetchData = async () => {
  loading.value = true;
  constructionData.value = [];
  try {
    const data_type = 'schedule'
    const response = await fetch(`http://59.110.65.210:8081/data?location=${selectedLocation.value}&data_type=${data_type}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    constructionData.value = data;
  } catch (error) {
    console.error("获取数据失败:", error);
  } finally {
    loading.value = false;
  }
};

watch(selectedLocation, () => {
  fetchData();
});

const safetyWarnings = ref<any[]>([]);
const delayWarnings = ref<any[]>([]);

const fetchSafetyWarnings = async () => {
  try {
    const response = await fetch('http://59.110.65.210:8081/alert');
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    safetyWarnings.value = await response.json();
  } catch (error) {
    console.error("获取安全事件预警数据失败:", error);
    safetyWarnings.value = [];
  }
};

const fetchDelayWarnings = async () => {
  try {
    const response = await fetch('http://59.110.65.210:8081/data?location=all&data_type=delay');
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    delayWarnings.value = await response.json();
  } catch (error) {
    console.error("获取施工进度超期数据失败:", error);
    delayWarnings.value = [];
  }
};


const progressData = ref<any[]>([]);
const progressFilterMapping = {
  '永年': {
    '桥台': {
      '0#Z-1': { l: 'yn', s: 'QT', t: '0#Z-1' },
      '0#Z-2': { l: 'yn', s: 'QT', t: '0#Z-2' },
      '0#Z-3': { l: 'yn', s: 'QT', t: '0#Z-3' },
      '11#Z-1': { l: 'yn', s: 'QT', t: '11#Z-1' },
      '11#Z-2': { l: 'yn', s: 'QT', t: '11#Z-2' },
      '11#Z-3': { l: 'yn', s: 'QT', t: '11#Z-3' }
    },
    '桥墩': {
      '1#Z-1': { l: 'yn', s: 'QD', t: '1#Z-1' },
      '1#Z-2': { l: 'yn', s: 'QD', t: '1#Z-2' },
      '1#Z-3': { l: 'yn', s: 'QD', t: '1#Z-3' },
      '2#Z-1': { l: 'yn', s: 'QD', t: '2#Z-1' },
      '2#Z-2': { l: 'yn', s: 'QD', t: '2#Z-2' },
      '2#Z-3': { l: 'yn', s: 'QD', t: '2#Z-3' },
      '3#Z-1': { l: 'yn', s: 'QD', t: '3#Z-1' },
      '3#Z-2': { l: 'yn', s: 'QD', t: '3#Z-2' },
      '3#Z-3': { l: 'yn', s: 'QD', t: '3#Z-3' },
      '4#Z-1': { l: 'yn', s: 'QD', t: '4#Z-1' },
      '4#Z-2': { l: 'yn', s: 'QD', t: '4#Z-2' },
      '4#Z-3': { l: 'yn', s: 'QD', t: '4#Z-3' },
      '5#Z-1': { l: 'yn', s: 'QD', t: '5#Z-1' },
      '5#Z-2': { l: 'yn', s: 'QD', t: '5#Z-2' },
      '5#Z-3': { l: 'yn', s: 'QD', t: '5#Z-3' },
      '6#Z-1': { l: 'yn', s: 'QD', t: '6#Z-1' },
      '6#Z-2': { l: 'yn', s: 'QD', t: '6#Z-2' },
      '6#Z-3': { l: 'yn', s: 'QD', t: '6#Z-3' },
      '7#Z-1': { l: 'yn', s: 'QD', t: '7#Z-1' },
      '7#Z-2': { l: 'yn', s: 'QD', t: '7#Z-2' },
      '7#Z-3': { l: 'yn', s: 'QD', t: '7#Z-3' },
      '8#Z-1': { l: 'yn', s: 'QD', t: '8#Z-1' },
      '8#Z-2': { l: 'yn', s: 'QD', t: '8#Z-2' },
      '8#Z-3': { l: 'yn', s: 'QD', t: '8#Z-3' },
      '9#Z-1': { l: 'yn', s: 'QD', t: '9#Z-1' },
      '9#Z-2': { l: 'yn', s: 'QD', t: '9#Z-2' },
      '9#Z-3': { l: 'yn', s: 'QD', t: '9#Z-3' },
      '10#Z-1': { l: 'yn', s: 'QD', t: '10#Z-1' },
      '10#Z-2': { l: 'yn', s: 'QD', t: '10#Z-2' }
    },
    '盖梁': {
      '0#': { l: 'yn', s: 'GL', t: '0#' },
      '1#': { l: 'yn', s: 'GL', t: '1#' },
      '2#': { l: 'yn', s: 'GL', t: '2#' },
      '3#': { l: 'yn', s: 'GL', t: '3#' },
      '4#': { l: 'yn', s: 'GL', t: '4#' },
      '5#': { l: 'yn', s: 'GL', t: '5#' },
      '6#': { l: 'yn', s: 'GL', t: '6#' },
      '7#': { l: 'yn', s: 'GL', t: '7#' },
      '8#': { l: 'yn', s: 'GL', t: '8#' },
      '9#': { l: 'yn', s: 'GL', t: '9#' },
      '10#': { l: 'yn', s: 'GL', t: '10#' },
      '11#': { l: 'yn', s: 'GL', t: '11#' }
    },
    '预制箱梁': {
      'XL1-1': { l: 'yn', s: 'YZL', t: 'XL1-1' },
      'XL1-2': { l: 'yn', s: 'YZL', t: 'XL1-2' },
      'XL1-3': { l: 'yn', s: 'YZL', t: 'XL1-3' },
      'XL1-4': { l: 'yn', s: 'YZL', t: 'XL1-4' },
      'XL1-5': { l: 'yn', s: 'YZL', t: 'XL1-5' },
      'XL2-1': { l: 'yn', s: 'YZL', t: 'XL2-1' },
      'XL2-2': { l: 'yn', s: 'YZL', t: 'XL2-2' },
      'XL2-3': { l: 'yn', s: 'YZL', t: 'XL2-3' },
      'XL2-4': { l: 'yn', s: 'YZL', t: 'XL2-4' },
      'XL2-5': { l: 'yn', s: 'YZL', t: 'XL2-5' },
      'XL3-1': { l: 'yn', s: 'YZL', t: 'XL3-1' },
      'XL3-2': { l: 'yn', s: 'YZL', t: 'XL3-2' },
      'XL3-3': { l: 'yn', s: 'YZL', t: 'XL3-3' },
      'XL3-4': { l: 'yn', s: 'YZL', t: 'XL3-4' },
      'XL3-5': { l: 'yn', s: 'YZL', t: 'XL3-5' },
      'XL4-1': { l: 'yn', s: 'YZL', t: 'XL4-1' },
      'XL4-2': { l: 'yn', s: 'YZL', t: 'XL4-2' },
      'XL4-3': { l: 'yn', s: 'YZL', t: 'XL4-3' },
      'XL4-4': { l: 'yn', s: 'YZL', t: 'XL4-4' },
      'XL4-5': { l: 'yn', s: 'YZL', t: 'XL4-5' },
      'XL5-1': { l: 'yn', s: 'YZL', t: 'XL5-1' },
      'XL5-2': { l: 'yn', s: 'YZL', t: 'XL5-2' },
      'XL5-3': { l: 'yn', s: 'YZL', t: 'XL5-3' },
      'XL5-4': { l: 'yn', s: 'YZL', t: 'XL5-4' },
      'XL5-5': { l: 'yn', s: 'YZL', t: 'XL5-5' },
      'XL6-1': { l: 'yn', s: 'YZL', t: 'XL6-1' },
      'XL6-2': { l: 'yn', s: 'YZL', t: 'XL6-2' },
      'XL6-3': { l: 'yn', s: 'YZL', t: 'XL6-3' },
      'XL6-4': { l: 'yn', s: 'YZL', t: 'XL6-4' },
      'XL6-5': { l: 'yn', s: 'YZL', t: 'XL6-5' }
    },
    '现浇箱梁': {
      'XL7': { l: 'yn', s: 'XJ', t: 'XL7' },
      'XL8': { l: 'yn', s: 'XJ', t: 'XL8' },
      'XL9': { l: 'yn', s: 'XJ', t: 'XL9' },
      'XL10': { l: 'yn', s: 'XJ', t: 'XL10' },
      'XL11': { l: 'yn', s: 'XJ', t: 'XL11' }
    },
    '桥面': {
      '护栏': { l: 'yn', s: 'QM', t: 'HL' },
      '水泥桥面铺装': { l: 'yn', s: 'QM', t: 'SNQMPZ' },
      '沥青桥面铺装': { l: 'yn', s: 'QM', t: 'LQQMPZ' },
      '横向湿接缝': { l: 'yn', s: 'QM', t: 'SJFH' },
      '纵向湿接缝': { l: 'yn', s: 'QM', t: 'SJFZ' }
    },
    '匝道': {
      'A': { l: 'yn', s: 'ZD', t: 'A' },
      'B': { l: 'yn', s: 'ZD', t: 'B' },
      'C': { l: 'yn', s: 'ZD', t: 'C' },
      'D': { l: 'yn', s: 'ZD', t: 'D' },
      'E': { l: 'yn', s: 'ZD', t: 'E' }
    },
    '通道': {
      'CK0+192.289': { l: 'yn', s: 'TD', t: 'CK0+192.289' },
      'EK0+185.5': { l: 'yn', s: 'TD', t: 'EK0+185.5' },
      'K410+077.744': { l: 'yn', s: 'TD', t: 'K410+077.744' },
      'K410+427.139': { l: 'yn', s: 'TD', t: 'K410+427.139' }
    },
    '涵洞': {
      'CK0+310': { l: 'yn', s: 'HD', t: 'CK0+310' },
      'DK0+280': { l: 'yn', s: 'HD', t: 'DK0+280' },
      'GK0+432': { l: 'yn', s: 'HD', t: 'GK0+432' }
    }
  },
  '肥乡北': {
    '桥台': {
      '0#Z-1': { l: 'fx_n', s: 'QT', t: '0#Z-1' },
      '0#Z-2': { l: 'fx_n', s: 'QT', t: '0#Z-2' },
      '0#Z-3': { l: 'fx_n', s: 'QT', t: '0#Z-3' },
      '4#Z-1': { l: 'fx_n', s: 'QT', t: '4#Z-1' },
      '4#Z-2': { l: 'fx_n', s: 'QT', t: '4#Z-2' },
      '4#Z-3': { l: 'fx_n', s: 'QT', t: '4#Z-3' }
    },
    '桥墩': {
      '1#Z-1': { l: 'fx_n', s: 'QD', t: '1#Z-1' },
      '1#Z-2': { l: 'fx_n', s: 'QD', t: '1#Z-2' },
      '1#Z-3': { l: 'fx_n', s: 'QD', t: '1#Z-3' },
      '2#Z-1': { l: 'fx_n', s: 'QD', t: '2#Z-1' },
      '2#Z-2': { l: 'fx_n', s: 'QD', t: '2#Z-2' },
      '2#Z-3': { l: 'fx_n', s: 'QD', t: '2#Z-3' },
      '3#Z-1': { l: 'fx_n', s: 'QD', t: '3#Z-1' },
      '3#Z-2': { l: 'fx_n', s: 'QD', t: '3#Z-2' },
      '3#Z-3': { l: 'fx_n', s: 'QD', t: '3#Z-3' }
    },
    '盖梁': {
      '0#': { l: 'fx_n', s: 'GL', t: '0#' },
      '1#': { l: 'fx_n', s: 'GL', t: '1#' },
      '2#': { l: 'fx_n', s: 'GL', t: '2#' },
      '3#': { l: 'fx_n', s: 'GL', t: '3#' },
      '4#': { l: 'fx_n', s: 'GL', t: '4#' }
    },
    '预制箱梁': {
      'XL1-1': { l: 'fx_n', s: 'YZL', t: 'XL1-1' },
      'XL1-2': { l: 'fx_n', s: 'YZL', t: 'XL1-2' },
      'XL1-3': { l: 'fx_n', s: 'YZL', t: 'XL1-3' },
      'XL1-4': { l: 'fx_n', s: 'YZL', t: 'XL1-4' },
      'XL1-5': { l: 'fx_n', s: 'YZL', t: 'XL1-5' },
      'XL2-1': { l: 'fx_n', s: 'YZL', t: 'XL2-1' },
      'XL2-2': { l: 'fx_n', s: 'YZL', t: 'XL2-2' },
      'XL2-3': { l: 'fx_n', s: 'YZL', t: 'XL2-3' },
      'XL2-4': { l: 'fx_n', s: 'YZL', t: 'XL2-4' },
      'XL2-5': { l: 'fx_n', s: 'YZL', t: 'XL2-5' },
      'XL3-1': { l: 'fx_n', s: 'YZL', t: 'XL3-1' },
      'XL3-2': { l: 'fx_n', s: 'YZL', t: 'XL3-2' },
      'XL3-3': { l: 'fx_n', s: 'YZL', t: 'XL3-3' },
      'XL3-4': { l: 'fx_n', s: 'YZL', t: 'XL3-4' },
      'XL3-5': { l: 'fx_n', s: 'YZL', t: 'XL3-5' },
      'XL4-1': { l: 'fx_n', s: 'YZL', t: 'XL4-1' },
      'XL4-2': { l: 'fx_n', s: 'YZL', t: 'XL4-2' },
      'XL4-3': { l: 'fx_n', s: 'YZL', t: 'XL4-3' },
      'XL4-4': { l: 'fx_n', s: 'YZL', t: 'XL4-4' },
      'XL4-5': { l: 'fx_n', s: 'YZL', t: 'XL4-5' }
    },
    '桥面': {
      '护栏': { l: 'fx_n', s: 'QM', t: 'HL' },
      '水泥桥面铺装': { l: 'fx_n', s: 'QM', t: 'SNQMPZ' },
      '沥青桥面铺装': { l: 'fx_n', s: 'QM', t: 'LQQMPZ' },
      '横向湿接缝': { l: 'fx_n', s: 'QM', t: 'SJFH' },
      '纵向湿接缝': { l: 'fx_n', s: 'QM', t: 'SJFZ' }
    },
    '匝道': {
      'A': { l: 'fx_n', s: 'ZD', t: 'A' },
      'B': { l: 'fx_n', s: 'ZD', t: 'B' },
      'C': { l: 'fx_n', s: 'ZD', t: 'C' },
      'D': { l: 'fx_n', s: 'ZD', t: 'D' },
      'E': { l: 'fx_n', s: 'ZD', t: 'E' },
      'F': { l: 'fx_n', s: 'ZD', t: 'F' },
      'G': { l: 'fx_n', s: 'ZD', t: 'G' },
      'H': { l: 'fx_n', s: 'ZD', t: 'H' },
      'I': { l: 'fx_n', s: 'ZD', t: 'I' }
    },
    '通道': {
      'K47+731.832': { l: 'fx_n', s: 'TD', t: 'K47+731.832' },
      'AK0+800': { l: 'fx_n', s: 'TD', t: 'AK0+800' }
    },
    '涵洞': {
      'BK0+370': { l: 'fx_n', s: 'HD', t: 'BK0+370' },
      'CK0+080': { l: 'fx_n', s: 'HD', t: 'CK0+080' },
      'DK0+310': { l: 'fx_n', s: 'HD', t: 'DK0+310' },
      'EK0+270': { l: 'fx_n', s: 'HD', t: 'EK0+270' },
      'FK0+070': { l: 'fx_n', s: 'HD', t: 'FK0+070' },
      'GK0+240': { l: 'fx_n', s: 'HD', t: 'GK0+240' },
      'HK0+300': { l: 'fx_n', s: 'HD', t: 'HK0+300' },
      'IK0+160': { l: 'fx_n', s: 'HD', t: 'IK0+160' }
    },
    '路肩墙': {
      'AK0+000-AK0+080': { l: 'fx_n', s: 'LJQ', t: 'AK0+000-AK0+080' }
    }
  },
  '肥乡南': {
    '桥台': {
      '0#Z-1': { l: 'fx_s', s: 'QT', t: '0#Z-1' },
      '0#Z-2': { l: 'fx_s', s: 'QT', t: '0#Z-2' },
      '0#Z-3': { l: 'fx_s', s: 'QT', t: '0#Z-3' },
      '5#Z-1': { l: 'fx_s', s: 'QT', t: '5#Z-1' },
      '5#Z-2': { l: 'fx_s', s: 'QT', t: '5#Z-2' },
      '5#Z-3': { l: 'fx_s', s: 'QT', t: '5#Z-3' }
    },
    '桥墩': {
      '1#Z-1': { l: 'fx_s', s: 'QD', t: '1#Z-1' },
      '1#Z-2': { l: 'fx_s', s: 'QD', t: '1#Z-2' },
      '1#Z-3': { l: 'fx_s', s: 'QD', t: '1#Z-3' },
      '2#Z-1': { l: 'fx_s', s: 'QD', t: '2#Z-1' },
      '2#Z-2': { l: 'fx_s', s: 'QD', t: '2#Z-2' },
      '2#Z-3': { l: 'fx_s', s: 'QD', t: '2#Z-3' },
      '3#Z-1': { l: 'fx_s', s: 'QD', t: '3#Z-1' },
      '3#Z-2': { l: 'fx_s', s: 'QD', t: '3#Z-2' },
      '3#Z-3': { l: 'fx_s', s: 'QD', t: '3#Z-3' },
      '4#Z-1': { l: 'fx_s', s: 'QD', t: '4#Z-1' },
      '4#Z-2': { l: 'fx_s', s: 'QD', t: '4#Z-2' },
      '4#Z-3': { l: 'fx_s', s: 'QD', t: '4#Z-3' }
    },
    '盖梁': {
      '0#': { l: 'fx_s', s: 'GL', t: '0#' },
      '1#': { l: 'fx_s', s: 'GL', t: '1#' },
      '2#': { l: 'fx_s', s: 'GL', t: '2#' },
      '3#': { l: 'fx_s', s: 'GL', t: '3#' },
      '4#': { l: 'fx_s', s: 'GL', t: '4#' },
      '5#': { l: 'fx_s', s: 'GL', t: '5#' }
    },
    '预制箱梁': {
      'XL1-1': { l: 'fx_s', s: 'YZL', t: 'XL1-1' },
      'XL1-2': { l: 'fx_s', s: 'YZL', t: 'XL1-2' },
      'XL1-3': { l: 'fx_s', s: 'YZL', t: 'XL1-3' },
      'XL1-4': { l: 'fx_s', s: 'YZL', t: 'XL1-4' },
      'XL1-5': { l: 'fx_s', s: 'YZL', t: 'XL1-5' },
      'XL2-1': { l: 'fx_s', s: 'YZL', t: 'XL2-1' },
      'XL2-2': { l: 'fx_s', s: 'YZL', t: 'XL2-2' },
      'XL2-3': { l: 'fx_s', s: 'YZL', t: 'XL2-3' },
      'XL2-4': { l: 'fx_s', s: 'YZL', t: 'XL2-4' },
      'XL2-5': { l: 'fx_s', s: 'YZL', t: 'XL2-5' },
      'XL3-1': { l: 'fx_s', s: 'YZL', t: 'XL3-1' },
      'XL3-2': { l: 'fx_s', s: 'YZL', t: 'XL3-2' },
      'XL3-3': { l: 'fx_s', s: 'YZL', t: 'XL3-3' },
      'XL3-4': { l: 'fx_s', s: 'YZL', t: 'XL3-4' },
      'XL3-5': { l: 'fx_s', s: 'YZL', t: 'XL3-5' },
      'XL4-1': { l: 'fx_s', s: 'YZL', t: 'XL4-1' },
      'XL4-2': { l: 'fx_s', s: 'YZL', t: 'XL4-2' },
      'XL4-3': { l: 'fx_s', s: 'YZL', t: 'XL4-3' },
      'XL4-4': { l: 'fx_s', s: 'YZL', t: 'XL4-4' },
      'XL4-5': { l: 'fx_s', s: 'YZL', t: 'XL4-5' },
      'XL5-1': { l: 'fx_s', s: 'YZL', t: 'XL5-1' },
      'XL5-2': { l: 'fx_s', s: 'YZL', t: 'XL5-2' },
      'XL5-3': { l: 'fx_s', s: 'YZL', t: 'XL5-3' },
      'XL5-4': { l: 'fx_s', s: 'YZL', t: 'XL5-4' },
      'XL5-5': { l: 'fx_s', s: 'YZL', t: 'XL5-5' }
    },
    '桥面': {
      '护栏': { l: 'fx_s', s: 'QM', t: 'HL' },
      '水泥桥面铺装': { l: 'fx_s', s: 'QM', t: 'SNQMPZ' },
      '沥青桥面铺装': { l: 'fx_s', s: 'QM', t: 'LQQMPZ' },
      '横向湿接缝': { l: 'fx_s', s: 'QM', t: 'SJFH' },
      '纵向湿接缝': { l: 'fx_s', s: 'QM', t: 'SJFZ' }
    },
    '匝道': {
      'A': { l: 'fx_s', s: 'ZD', t: 'A' },
      'B': { l: 'fx_s', s: 'ZD', t: 'B' },
      'C': { l: 'fx_s', s: 'ZD', t: 'C' },
      'D': { l: 'fx_s', s: 'ZD', t: 'D' },
      'E': { l: 'fx_s', s: 'ZD', t: 'E' },
      'F': { l: 'fx_s', s: 'ZD', t: 'F' },
      'G': { l: 'fx_s', s: 'ZD', t: 'G' },
      'H': { l: 'fx_s', s: 'ZD', t: 'H' },
      'I': { l: 'fx_s', s: 'ZD', t: 'I' }
    },
    '通道': {
      'K47+731.832': { l: 'fx_s', s: 'TD', t: 'K47+731.832' },
      'AK0+800': { l: 'fx_s', s: 'TD', t: 'AK0+800' }
    },
    '涵洞': {
      'BK0+370': { l: 'fx_s', s: 'HD', t: 'BK0+370' },
      'CK0+080': { l: 'fx_s', s: 'HD', t: 'CK0+080' },
      'DK0+310': { l: 'fx_s', s: 'HD', t: 'DK0+310' },
      'EK0+270': { l: 'fx_s', s: 'HD', t: 'EK0+270' },
      'FK0+070': { l: 'fx_s', s: 'HD', t: 'FK0+070' },
      'GK0+240': { l: 'fx_s', s: 'HD', t: 'GK0+240' },
      'HK0+300': { l: 'fx_s', s: 'HD', t: 'HK0+300' },
      'IK0+160': { l: 'fx_s', s: 'HD', t: 'IK0+160' }
    },
    '路肩墙': {
      'AK0+830-AK0+869.718': { l: 'fx_s', s: 'LJQ', t: 'AK0+830-AK0+869.718' }
    }
  }
};
const progressFilters = ref({
  location: '永年',
  structure: '匝道',
  model: 'A'
});

const fetchProgressData = async () => {
  const { location, structure, model } = progressFilters.value;

  if (location && structure && model) {
    try {
      const locationMap = progressFilterMapping[location as keyof typeof progressFilterMapping];
      const structureMap = locationMap[structure as keyof typeof locationMap];
      const params = structureMap[model as keyof typeof structureMap];
      if (!params) return;

      const encodedType = encodeURIComponent(params.t).replace(/%2B/g, '%2B').replace(/%23/g, '%23');
      const url = `http://59.110.65.210:8081/query?location=${params.l}&structure=${params.s}&type=${encodedType}`;
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const textData = await response.text();
      let data;
      try {
        data = JSON.parse(textData);
      } catch (e) {
        data = null;
      }

      if (Array.isArray(data)) {
        progressData.value = data.map((item: any) => ({
          ...item,
          location: location,
          structure: structure + '-' + model,
        }));
      } else {
        progressData.value = [{
          location: location,
          structure: structure + '-' + model,
          state: '未开工',
          start_date: '-',
          end_date: '-'
        }];
      }

    } catch (error) {
      console.error("获取施工进度数据失败:", error);
      progressData.value = [];
    }
  }
};

const progressLocations = computed(() => Object.keys(progressFilterMapping));
const progressStructures = computed(() => {
  const loc = progressFilters.value.location as keyof typeof progressFilterMapping;
  return Object.keys(progressFilterMapping[loc]);
});
const progressModels = computed(() => {
  const loc = progressFilters.value.location as keyof typeof progressFilterMapping;
  const struc = progressFilters.value.structure as keyof typeof progressFilterMapping[typeof loc];
  const structureMap = progressFilterMapping[loc]?.[struc];
  return structureMap ? Object.keys(structureMap) : [];
});

watch(() => progressFilters.value.location, (newLocation) => {
  const newStructures = Object.keys(progressFilterMapping[newLocation as keyof typeof progressFilterMapping]);
  progressFilters.value.structure = newStructures[0] || '';
});

watch(() => progressFilters.value.structure, (newStructure, oldStructure) => {
    if (newStructure !== oldStructure) {
        const loc = progressFilters.value.location as keyof typeof progressFilterMapping;
        const struc = newStructure as keyof typeof progressFilterMapping[typeof loc];
        const newModels = Object.keys(progressFilterMapping[loc]?.[struc] || {});
        progressFilters.value.model = newModels[0] || '';
    }
}, { immediate: true });

watch(progressFilters, () => {
  fetchProgressData();
}, { deep: true });


onMounted(async () => {
  try {
    allDataLoaded.value = false; 
    console.log("Fetching data sequentially...");

    // 串行获取所有数据
    await fetchData();
    console.log("Completed: fetchData");

    await fetchProgressData();
    console.log("Completed: fetchProgressData");

    await fetchSafetyWarnings();
    console.log("Completed: fetchSafetyWarnings");

    await fetchDelayWarnings();
    console.log("Completed: fetchDelayWarnings");

  } catch (error) {
    console.error("An error occurred during sequential data fetching:", error);
  } finally {
    allDataLoaded.value = true; 
    console.log("All data fetching routines completed. Rendering components.");
  }
  if (dataScreenRef.value) {
    dataScreenRef.value.style.transform = `scale(${getScale()}) translate(-50%, -50%)`;
    dataScreenRef.value.style.width = `1920px`;
    dataScreenRef.value.style.height = `1080px`;
  }
  window.addEventListener("resize", resize);
});

const resize = () => {
  if (dataScreenRef.value) {
    dataScreenRef.value.style.transform = `scale(${getScale()}) translate(-50%, -50%)`;
  }
};

const getScale = (width = 1920, height = 1080) => {
  let ww = window.innerWidth / width;
  let wh = window.innerHeight / height;
  return ww < wh ? ww : wh;
};

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

.lf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px 0 0;
}

.location-filter select,
.filters select {
  background-color: rgba(0, 0, 0, 0.3);
  color: #fff;
  border: 1px solid #05e8fe;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 15px;
  outline: none;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-left: 10px;
}

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

.loading-text {
  color: #fff;
  width: 100%;
  text-align: center;
  margin-top: 50px;
}

.custom-table-container {
  height: 100%;
  overflow-y: auto;
  
  &.table-20-rows {
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
  font-size: 13px;
  
  thead tr {
    background-color: transparent;
    position: sticky;
    top: 0;
    z-index: 1;
  }
  
  th {
    background: #0d2a42;
    padding: 8px;
    text-align: center;
    border-bottom: 1px solid rgba(5, 232, 254, 0.1);
    white-space: nowrap;
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 10px 0 0;
}

.filters {
  display: flex;
  gap: 5px;
}

.loading-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(13, 42, 66, 0.8);
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  color: #fff;
}

.loading-spinner {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: 8px solid rgba(255, 255, 255, 0.2);
  border-top-color: #05e8fe;
  animation: spin 1s linear infinite;
}

.loading-text {
  margin-top: 20px;
  font-size: 20px;
  font-weight: 500;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

@keyframes spin {
  from {
    transform: rotate(0deg); /* 从 0 度开始 */
  }
  to {
    transform: rotate(360deg); /* 旋转到 360 度 */
  }
}
</style>
