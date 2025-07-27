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
  margin: 0;
  padding: 0;
  overflow: hidden;
}

html, body {
  height: 100%;
  width: 100%;
}

#app {
  margin: 0 auto;
  height: 100vh;
  width: 100vw;
}
</style>