<template>
  <div ref="eChartsRef" class="echarts" :style="echartsStyle"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import echarts from './config';
import type { ECOption } from './config';

interface Props {
  option: ECOption;
  resize?: boolean;
  width?: string | number;
  height?: string | number;
}

const props = withDefaults(defineProps<Props>(), {
  resize: true,
  width: '100%',
  height: '100%'
});

const eChartsRef = ref<HTMLElement>();
let chartInstance: echarts.ECharts | null = null;

const echartsStyle = computed(() => ({
  width: typeof props.width === 'number' ? `${props.width}px` : props.width,
  height: typeof props.height === 'number' ? `${props.height}px` : props.height
}));

const initChart = () => {
  if (eChartsRef.value) {
    chartInstance = echarts.init(eChartsRef.value);
    chartInstance.setOption(props.option);
  }
};

const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize();
  }
};

watch(() => props.option, (newOption) => {
  if (chartInstance) {
    chartInstance.setOption(newOption, true);
  }
}, { deep: true });

onMounted(() => {
  initChart();
  if (props.resize) {
    window.addEventListener('resize', resizeChart);
  }
});

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
  if (props.resize) {
    window.removeEventListener('resize', resizeChart);
  }
});
</script>

<style scoped>
.echarts {
  width: 100%;
  height: 100%;
}
</style>