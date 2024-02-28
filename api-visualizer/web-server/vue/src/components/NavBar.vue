<template>
  <b-navbar variant="info" class="w-100">
    <b-navbar-brand>MahjongSoul API Visualizer</b-navbar-brand>
    <b-navbar-nav class="ml-auto">
      <b-nav-item href="/mitmproxy-ca-cert.crt">Certificate</b-nav-item>
      <b-nav-item>Log</b-nav-item>
      <b-form-checkbox v-model="debugMode">Debug mode</b-form-checkbox>
    </b-navbar-nav>
  </b-navbar>
</template>

<script>
export default {
  name: 'Navbar',

  props: {
    setDebugMode: Function
  },

  data() {
    return {
      debugMode_: false
    }
  },

  computed: {
    debugMode: {
      set(value) {
        this.setDebugMode(value);
        this.debugMode_ = value;
      },
      get() {
        return this.debugMode_;
      }
    }
  }
}
</script>

<style>
</style>
