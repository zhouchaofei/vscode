<template>
  <DataScreen />
</template>

<script>
import { defineComponent } from 'vue';
import DataScreen from './DataScreen.vue';

export default defineComponent({
  name: 'App',
  components: {
    DataScreen
  }
});
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  overflow: hidden;
}
</style>