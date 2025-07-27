<template>
  <div id="app">
    <DataScreen />
  </div>
</template>

<script>
import DataScreen from './views/dataScreen/index.vue'

export default {
  components: {
    DataScreen
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  min-height: 100vh;
}

#app {
  margin: 0 auto;
}
</style>