<template>
  <div class="chart-wrapper">
    <div class="echarts-container">
      <ECharts :option="option" :resize="false" />
    </div>
    <div class="info-container" v-if="chartData">
      <p>未完成数量: {{ chartData.countOfUnfinished }}</p>
      <p>{{ consNameMap[chartData.cons] || chartData.cons }}已开展时长为: {{ chartData.duration_percent }}</p>
      <p>计划完工日期为: {{ chartData.end_date_plan }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import ECharts from "@/components/ECharts/index.vue";
import { ECOption } from "@/components/ECharts/config";

// 0. 定义一个中文名称的映射表，让显示更友好
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

// 1. 定义 props 来接收来自父组件的数据
// 'chartData' 将会是 data.json 中数组的一个元素
const props = defineProps<{
  chartData: {
    location: string;  //地点
    cons: string;   //施工内容
    // start_date_plan: string;  // 计划开始日期
    end_date_plan: string;  // 计划结束日期
    current_date: string;  // 当前日期
    duration_cons: string;  // 实际施工时长
    duration_plan: string;  // 计划施工时长
    duration_percent: string;  // 实际施工时长占计划施工时长的百分比
    total_count: string;  // 总数量
    state_count: string;  // 已完成数量
    complete_percent: string;  // 完成百分比
    un_complete_percent: string;  // 未完成百分比
    countOfUnfinished: string;  // 未完成数量
  };
}>();

// 2. 使用 computed 来动态生成 option，这样当 props 变化时，图表会自动更新
const option = computed<ECOption>(() => {
  // 如果没有数据，返回一个空配置
  if (!props.chartData) {
    return {};
  }

  // 从 props 中解析数据
  const finishedValue = parseInt(props.chartData.state_count) || 0;
  const unfinishedValue = parseInt(props.chartData.countOfUnfinished) || 0;
  const finishedPercent = parseInt(props.chartData.complete_percent) || 0;
  const unfinishedPercent = parseInt(props.chartData.un_complete_percent) || 0;

  // 饼图的数据，现在是 “已完成” 和 “未完成”
  const seriesData = [
    { value: finishedValue, name: "已完成", percentage: `${finishedPercent}%` },
    { value: unfinishedValue, name: "未完成" }
  ];

  // 饼图的颜色
  const colors = ["#F6C95C", "#1F9393"];

  return {
    color: colors,
    tooltip: {
      trigger: "item",
      formatter: "{b}: {c} ({d}%)" // 提示框格式：名称: 数量 (百分比%)
    },
    // 3. 移除了旧的 legend 配置，因为我们用独立的 div 来展示信息

    series: [
      {
        // zlevel: 1,
        name: "完成度",
        type: "pie",
        // selectedMode: "single",
        // 4. 缩小饼图半径并调整中心位置，使其适应新布局
        radius: ['60%', '80%'], // 使用百分比可以让它更好地适应容器
        center: ["50%", "50%"],
        // startAngle: 60,
        avoidLabelOverlap: false,
        label: {
                        // show: false, // 不在扇区上显示标签
                        // position: "center",
          position: "inside",
          show: true,
          color: "#fff",
          formatter: function (params) {
            return (params.data as seriesData).percentage;
          },
          rich: {
            b: {
              fontSize: 16,
              lineHeight: 30,
              color: "#fff"
            }
          }
        },
        itemStyle: {
          shadowColor: "rgba(0, 0, 0, 0.2)",
          shadowBlur: 10
        },
        emphasis: { // 高亮状态（鼠标悬停）时，在中间显示文字
          label: {
            show: true,
            fontSize: 14,
            fontWeight: "bold",
            formatter: "{b}\n{d}%" // 格式：名称\n百分比
          }
        },
        labelLine: {
          show: false
        },
        data: seriesData
      },
      {
        name: "",
        type: "pie",
        selectedMode: "single",
        radius: ['60%', '80%'],
        center: ["50%", "50%"],
        startAngle: 60,
        data: [
          {
            value: 1000,
            name: "",
            label: {
              show: true,
              formatter: "{a|总数量}",
              rich: {
                a: {
                  align: "center",
                  color: "rgb(98,137,169)",
                  fontSize: 14
                }
              },
              position: "center"
            }
          }
        ]
      }
    ]
  };
});
</script>

<style lang="scss" scoped>
/* 6. 更新样式以适应新布局 */
.chart-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 5px;
  box-sizing: border-box;
}

.echarts-container {
  width: 50%;
  height: 100%;
}

.info-container {
  width: 50%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  font-size: 12px;
  color: #fff;
  padding-left: 10px;
  line-height: 1.5;
  white-space: normal;
  word-break: break-all;
}
</style>

<template>
  <!-- 完成和未完成数量比例 -->
  <div class="echarts">
    <ECharts :option="option" :resize="false" />
  </div>
</template>

<script setup lang="ts">
import ECharts from "@/components/ECharts/index.vue";
import { ECOption } from "@/components/ECharts/config";

interface ChartProp {
  value: number;
  name: string;
  percentage: string;
}

// 1. 数据已更新为两个分类：“30岁以下” 和 “30岁以上”
let data: ChartProp[] = [
  { value: 460, name: "30岁以下", percentage: "36%" },
  { value: 820, name: "30岁以上", percentage: "64%" }
];

const colors = ["#F6C95C", "#184EA1"];
// const colors = ["#F6C95C", "#EF7D33", "#1F9393", "#184EA1", "#81C8EF", "#9270CA"];

const option: ECOption = {
  color: colors,
  tooltip: {
    show: true,
    trigger: "item",
    formatter: "{b} <br/>占比：{d}%"
  },
  grid: { top: "bottom", left: 10, bottom: 10 },
  series: [
    {
      zlevel: 1,
      name: "年龄比例",
      type: "pie",
      selectedMode: "single",
      radius: [50, 90],
      center: ["35%", "50%"],
      startAngle: 60,
      label: {
        position: "inside",
        show: true,
        color: "#fff",
        formatter: function (params) {
          return (params.data as ChartProp).percentage;
        },
        rich: {
          b: {
            fontSize: 16,
            lineHeight: 30,
            color: "#fff"
          }
        }
      },
      itemStyle: {
        shadowColor: "rgba(0, 0, 0, 0.2)",
        shadowBlur: 10
      },
      data: data.map((val: ChartProp, index: number) => {
        return {
          value: val.value,
          name: val.name,
          percentage: val.percentage,
          itemStyle: {
            borderWidth: 10,
            shadowBlur: 20,
            borderColor: colors[index],
            borderRadius: 10
          }
        };
      })
    },
    {
      name: "",
      type: "pie",
      selectedMode: "single",
      radius: [50, 90],
      center: ["35%", "50%"],
      startAngle: 60,
      data: [
        {
          value: 1000,
          name: "",
          label: {
            show: true,
            formatter: "{a|总数量}",
            rich: {
              a: {
                align: "center",
                color: "rgb(98,137,169)",
                fontSize: 14
              }
            },
            position: "center"
          }
        }
      ]
    }
  ]
};
</script>
<style lang="scss" scoped>
.echarts {
  width: 100%;
  height: 100%;
}
</style>
