<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  setDebugMode: {
    type: Function,
    required: true,
  },
});

const debugMode_ = ref(false);

const debugMode = computed({
  get: () => debugMode_.value,
  set: (value) => {
    props.setDebugMode(value);
    debugMode_.value = value;
  },
});
</script>

<template>
  <b-navbar variant="info" class="w-100">
    <b-navbar-brand>MahjongSoul API Visualizer</b-navbar-brand>
    <b-navbar-nav class="ml-auto">
      <b-nav-item href="/mitmproxy-ca-cert.crt"> Certificate </b-nav-item>
      <b-nav-item>Log</b-nav-item>
      <b-form-checkbox v-model="debugMode"> Debug mode </b-form-checkbox>
    </b-navbar-nav>
  </b-navbar>
</template>

<style></style>
