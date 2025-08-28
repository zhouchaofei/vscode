<template>
  <div class="chart-container">
    <div class="echarts">
      <ECharts :option="option" :resize="false" />
    </div>
    <div class="info-panel" v-if="props.chartData">
      <p>未完成数量: {{ props.chartData.uncomplete_count }}</p>
      <p>{{ formattedConsNameForInfo }}已开展时长: {{ props.chartData.duration_percent }}</p>
      <p>计划完工日期: {{ props.chartData.end_date_plan }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import ECharts from "@/components/ECharts/index.vue";
import { ECOption } from "@/components/ECharts/config";

const consNameMap: { [key: string]: string } = {
  Z: "桥墩",
  GL: "盖梁",
  YZL_5: "预制梁完成",
  YZL_6: "预制梁吊装",
  ZD_1: "匝道路基填筑",
  ZD_4: "匝道完成",
  TD: "通道完成",
  HD: "涵洞完成"
};

const props = defineProps<{
  chartData: {
    cons: string;
    complete_percent: string;
    un_complete_percent: string;
    uncomplete_count: string;
    duration_percent: string;
    end_date_plan: string;
  };
}>();

const formattedConsName = computed(() => {
  const cons = props.chartData.cons;
  if (!cons) return "";

  const firstUnderscoreIndex = cons.indexOf("_");

  // 检查是否存在 "数字_" 前缀
  if (firstUnderscoreIndex > 0) {
    const bridgeNumber = cons.substring(0, firstUnderscoreIndex);
    const consCode = cons.substring(firstUnderscoreIndex + 1);

    const bridgeNameMap: { [key: string]: string } = {
      "1": "一号桥",
      "2": "二号桥"
    };

    const targetConsCodes = ["Z", "GL", "YZL_5", "YZL_6"];

    if (bridgeNameMap[bridgeNumber] && consNameMap[consCode] && targetConsCodes.includes(consCode)) {
      return `${bridgeNameMap[bridgeNumber]}\n${consNameMap[consCode]}`;
    }
  }

  // 如果不匹配 "数字_" 前缀规则，则使用原始的映射
  return consNameMap[cons] || cons;
});

const formattedConsNameForInfo = computed(() => {
    return formattedConsName.value.replace('\n', '');
});

const colors = ["#F6C95C", "#184EA1"];

// 动态生成option
const option = computed<ECOption>(() => {
  const completeValue = parseFloat(props.chartData.complete_percent) || 0;
  const uncompleteValue = parseFloat(props.chartData.un_complete_percent) || 0;

  // 过滤掉值为0的数据
  const seriesData = [
    { value: completeValue, name: "已完成", color: colors[0] },
    { value: uncompleteValue, name: "未完成", color: colors[1] }
  ].filter(item => item.value > 0);

  return {
    color: seriesData.map(item => item.color),
    tooltip: {
      show: true,
      trigger: "item",
      formatter: "{b}: {d}%"
    },
    series: [
      {
        zlevel: 1,
        name: "完成度",
        type: "pie",
        radius: [40, 70],
        center: ["50%", "50%"],
        startAngle: 90,
        label: {
          show: true,
          position: "inside",
          formatter: (params) => {
            if (params.value === 0) {
              return "";
            }
            return `${params.percent}%`;
          },
          color: "#fff",
          fontSize: 14
        },
        itemStyle: {
          shadowColor: "rgba(0, 0, 0, 0.2)",
          shadowBlur: 10
        },
        data: seriesData.map((val, index) => {
          return {
            value: val.value,
            name: val.name,
            itemStyle: {
              borderWidth: 10,
              shadowBlur: 20,
              borderColor: val.color,
              borderRadius: 10
            }
          };
        })
      },
      {
        name: "项目名称",
        type: "pie",
        radius: [40, 70], 
        center: ["50%", "50%"],
        labelLine: { show: false },
        data: [
          {
            value: 0,
            name: "",
            label: {
              show: true,
              position: "center",
              formatter: formattedConsName.value,
              color: "#ffffff",
              fontSize: 12,
              fontWeight: "bold",
              lineHeight: 16,
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
  flex-direction: column;
  align-items: center;
}

.echarts {
  width: 100%;
  height: 100%;
  flex: 1;
  min-height: 0;
}

.info-panel {
  width: 100%;
  text-align: center;
  color: #fff;
  font-size: 11px;
  line-height: 1.4;
  padding: 0 5px 15px 5px;
  box-sizing: border-box;

  p {
    margin: 0;
    padding: 0;
    white-space: normal;
    word-break: break-all;
  }
}
</style>
