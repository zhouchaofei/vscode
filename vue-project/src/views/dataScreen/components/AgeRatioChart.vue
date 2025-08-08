<template>
  <div class="chart-container">
    <div class="echarts">
      <ECharts :option="option" :resize="false" />
    </div>
    <div class="info-panel" v-if="props.chartData">
      <p>未完成数量: {{ props.chartData.countOfUnfinished }}</p>
      <p>{{ consNameMap[props.chartData.cons] || props.chartData.cons }}已开展时长: {{ props.chartData.duration_percent }}</p>
      <p>计划完工日期: {{ props.chartData.end_date_plan }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import ECharts from "@/components/ECharts/index.vue";
import { ECOption } from "@/components/ECharts/config";

// 定义一个中文名称的映射表，让显示更友好
const consNameMap: { [key: string]: string } = {
  Z: "桥墩",
  GL: "盖梁",
  YZL_5: "预制梁完成",
  YZL_6: "预制梁吊装",
  ZD_1: "匝道开挖台阶",
  ZD_4: "匝道完成",
  TD: "通道完成",
  HD: "涵洞完成"
};

// 定义props来接收来自父组件(index.vue)的数据
const props = defineProps<{
  chartData: {
    cons: string;
    complete_percent: string;
    un_complete_percent: string;
    countOfUnfinished: string;
    duration_percent: string;
    end_date_plan: string;
  };
}>();

const colors = ["#F6C95C", "#184EA1"]; // 黄色代表完成，蓝色代表未完成

// 使用computed来动态生成option，这样当props变化时，图表会自动更新
const option = computed<ECOption>(() => {
  // 从props中解析数据，并将百分比字符串转为数字（去掉'%'）
  const completeValue = parseFloat(props.chartData.complete_percent) || 0;
  const uncompleteValue = parseFloat(props.chartData.un_complete_percent) || 0;

  // const seriesData = [
  //   { value: completeValue, name: "已完成" },
  //   { value: uncompleteValue, name: "未完成" }
  // ];
  // 过滤掉值为0的数据
  const seriesData = [
    { value: completeValue, name: "已完成", color: colors[0] },
    { value: uncompleteValue, name: "未完成", color: colors[1] }
  ].filter(item => item.value > 0);

  return {
    // color: colors,
    color: seriesData.map(item => item.color), // 动态设置颜色
    tooltip: {
      show: true,
      trigger: "item",
      formatter: "{b}: {d}%" // 提示框显示 "已完成: 82%"
    },
    series: [
      // 第一个 series：负责渲染数据扇区和百分比
      {
        zlevel: 1,
        name: "完成度",
        type: "pie",
        // 恢复原始尺寸和位置
        radius: [40, 70],
        center: ["50%", "50%"],
        startAngle: 90,
        // 3. 在每个扇形上显示百分比
        label: {
          show: true,
          position: "inside",
          // formatter: "{d}%", // ECharts 内置格式化，直接显示百分比
          formatter: (params) => {
            if (params.value === 0) {
              return "";
            }
            return `${params.percent}%`;
          },
          color: "#fff",
          fontSize: 14
        },
        itemStyle: { // 保留阴影效果
          shadowColor: "rgba(0, 0, 0, 0.2)",
          shadowBlur: 10
        },
        data: seriesData.map((val, index) => {
          return {
            // ...val,
            value: val.value,
            name: val.name,
            itemStyle: { // 4. 恢复扇区边框样式
              borderWidth: 10,
              shadowBlur: 20,
              // borderColor: colors[index],
              borderColor: val.color, // 直接使用数据中定义的颜色
              borderRadius: 10
            }
          };
        })
      },
      // 1. 第二个 series：恢复，并用其在中心显示项目名称
      {
        name: "项目名称",
        type: "pie",
        radius: [40, 70], // 尺寸与第一个 series 相同以实现覆盖
        center: ["50%", "50%"],
        // silent: true, // 设置为静默，不响应鼠标事件
        labelLine: { show: false }, // 不显示标签线
        data: [
          {
            value: 0, // 虚拟数据，不影响布局
            name: "",
            label: {
              show: true,
              position: "center",
              // 2. 在中心显示项目中文名
              formatter: consNameMap[props.chartData.cons] || props.chartData.cons,
              color: "#ffffff",
              fontSize: 12,
              fontWeight: "bold"
            }
          }
        ]
      }
    ]
  };
});
</script>
<style lang="scss" scoped>
.chart-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column; // 设置为垂直布局
  align-items: center;
}

.echarts {
  width: 100%;
  height: 100%;
  flex: 1; // 图表区域占据大部分空间
  min-height: 0; // flex布局中的重要技巧，防止子元素溢出
}

.info-panel {
  width: 100%;
  text-align: center;
  color: #fff;
  font-size: 13px;
  line-height: 1.4;
  padding: 0 5px 5px 5px; // 底部留出一些空间
  box-sizing: border-box;

  p {
    margin: 0;
    padding: 0;
    white-space: normal;
    word-break: break-all;
  }
}
</style>
