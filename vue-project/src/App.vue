<template>
  <div class="app">
    <!-- <header>
      <h1>智慧监管平台</h1>
    </header> -->
    
    <!-- <VideoAnnotator /> -->
    <VideoTest />
  </div>
</template>

<script>
// import VideoAnnotator from './components/VideoAnnotator.vue'

// export default {
//   components: {
//     VideoAnnotator
//   }
// }
import VideoTest from './components/VideoTest.vue'

export default {
  components: {
    VideoTest
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
  /* background: linear-gradient(135deg, #1a2a6c, #b21f1f, #1a2a6c); */
  /* color: #fff; */
  /* min-height: 100vh; */
  /* padding: 20px; */
}

#app {
  /* max-width: 1200px; */
  margin: 0 auto;
  /* padding: 20px; */
}

/* header { */
  /* text-align: center;
  margin-bottom: 10px; */
  /* padding: 20px; */
  /* background: rgba(0, 0, 0, 0.3);
  border-radius: 15px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); */
/* } */

/* h1 { */
  /* font-size: 2.8rem; */
  /* margin-bottom: 10px; */
  /* background: linear-gradient(90deg, #ff8a00, #e52e71);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); */
/* } */
</style>