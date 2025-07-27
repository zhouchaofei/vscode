<template>
  <!-- 男女比例 -->
  <div class="ratio-main">
    <div class="ratio-header">
      <div class="man">
        <span>男士</span>
        <img src="../images/man.png" alt="" />
      </div>
      <div class="woman">
        <span>女士</span>
        <img src="../images/woman.png" alt="" />
      </div>
    </div>
    <!-- echarts -->
    <div class="echarts">
      <ECharts :option="option" :resize="false" />
    </div>
  </div>
</template>

<script setup>
import ECharts from "../../../components/ECharts.vue";

let data = {
  man: 60,
  woman: 40
};

const option = {
  color: ["#28B4F1", "#F468A0"],
  tooltip: {
    show: true,
    trigger: "item",
    formatter: "{b}: {c}%"
  },
  legend: {
    show: false
  },
  series: [
    {
      name: "男女比例",
      type: "pie",
      radius: ["30%", "70%"],
      center: ["50%", "60%"],
      label: {
        show: true,
        position: "outside",
        formatter: "{b}\n{c}%",
        fontSize: 12,
        color: "#fff"
      },
      labelLine: {
        show: true,
        length: 10,
        length2: 20
      },
      data: [
        { value: data.man, name: "男士" },
        { value: data.woman, name: "女士" }
      ]
    }
  ]
};
</script>

<style lang="scss" scoped>
.ratio-main {
  height: 100%;
  .ratio-header {
    display: flex;
    justify-content: space-around;
    align-items: center;
    margin-bottom: 10px;
    .man,
    .woman {
      display: flex;
      flex-direction: column;
      align-items: center;
      color: #fff;
      font-size: 12px;
      img {
        width: 30px;
        height: 30px;
        margin-top: 5px;
      }
    }
  }
  .echarts {
    width: 100%;
    height: calc(100% - 60px);
  }
}
</style>