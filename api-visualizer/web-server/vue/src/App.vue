<template>
  <div id="app" class="vh-100 p-0 d-flex flex-column">
    <NavBar :set-debug-mode="setDebugMode" />
    <!-- I don't know why `min-height: 0%;` is necessary, but the page is not
         rendered as expected without this `min-height`. See
         https://stackoverflow.com/questions/41570673 and
         https://github.com/twbs/bootstrap/issues/22339 for detail. -->
    <div class="flex-grow-1 flex-shrink-1 d-flex" style="min-height: 0%">
      <div class="col-4 mh-100 p-0" style="overflow-y: scroll">
        <ApiCallListView :set-detail-view="setDetailView" />
      </div>
      <div class="col-8 mh-100" style="overflow-y: auto">
        <ApiCallDetailView :data="dataForDetailView" :debug-mode="debugMode" />
      </div>
    </div>
  </div>
</template>

<script>
import NavBar from "./components/NavBar.vue";
import ApiCallListView from "./components/ApiCallListView.vue";
import ApiCallDetailView from "./components/ApiCallDetailView.vue";

export default {
  name: "App",

  components: {
    NavBar,
    ApiCallListView,
    ApiCallDetailView,
  },

  data() {
    const self = this;

    return {
      debugMode: false,

      setDebugMode(value) {
        self.debugMode = value;
      },

      dataForDetailView: null,

      setDetailView(data) {
        self.dataForDetailView = data;
      },
    };
  },
};
</script>

<style></style>
