<template>
  <div class="echarts">
    <ECharts :option="option" :resize="false" />
  </div>
</template>

<script setup>
import ECharts from "../../../components/ECharts.vue";

// Generate mock data for 30 days
const generateData = () => {
  const data = [];
  const categories = [];
  for (let i = 1; i <= 30; i++) {
    categories.push(`${i}日`);
    data.push(Math.floor(Math.random() * 5000) + 3000);
  }
  return { data, categories };
};

const { data, categories } = generateData();

const option = {
  grid: {
    top: "10%",
    left: "3%",
    right: "4%",
    bottom: "10%",
    containLabel: true
  },
  xAxis: {
    type: "category",
    data: categories,
    axisLine: {
      lineStyle: {
        color: "#28B4F1"
      }
    },
    axisLabel: {
      color: "#fff",
      fontSize: 10
    }
  },
  yAxis: {
    type: "value",
    axisLine: {
      lineStyle: {
        color: "#28B4F1"
      }
    },
    axisLabel: {
      color: "#fff",
      fontSize: 10
    },
    splitLine: {
      lineStyle: {
        color: "rgba(40, 180, 241, 0.2)"
      }
    }
  },
  series: [
    {
      name: "游客量",
      type: "line",
      data: data,
      smooth: true,
      lineStyle: {
        color: "#28B4F1",
        width: 2
      },
      itemStyle: {
        color: "#28B4F1"
      },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: "rgba(40, 180, 241, 0.8)" },
            { offset: 1, color: "rgba(40, 180, 241, 0.1)" }
          ]
        }
      }
    }
  ],
  tooltip: {
    trigger: "axis",
    backgroundColor: "rgba(0, 0, 0, 0.8)",
    borderColor: "#28B4F1",
    textStyle: {
      color: "#fff"
    }
  }
};
</script>

<style lang="scss" scoped>
.echarts {
  width: 100%;
  height: 100%;
}
</style>