<template>
  <div ref="chartRef" :style="{ width: '100%', height: '100%' }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import 'echarts-liquidfill'

const props = defineProps({
  option: {
    type: Object,
    required: true
  },
  resize: {
    type: Boolean,
    default: true
  }
})

const chartRef = ref(null)
let chartInstance = null

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  chartInstance.setOption(props.option)
}

const resizeChart = () => {
  if (chartInstance && props.resize) {
    chartInstance.resize()
  }
}

onMounted(() => {
  initChart()
  if (props.resize) {
    window.addEventListener('resize', resizeChart)
  }
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  window.removeEventListener('resize', resizeChart)
})

watch(() => props.option, (newOption) => {
  if (chartInstance) {
    chartInstance.setOption(newOption, true)
  }
}, { deep: true })
</script>