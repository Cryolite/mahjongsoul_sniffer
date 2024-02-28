import { createApp } from "vue";
import { createBootstrap } from "bootstrap-vue-next";
import App from "./App.vue";

// Import Bootstrap an BootstrapVue CSS files (order is important)
import "bootstrap/dist/css/bootstrap.css";
import "bootstrap-vue-next/dist/bootstrap-vue-next.css";

import JsonViewer from "vue3-json-viewer";
import "vue3-json-viewer/dist/index.css";

const app = createApp(App);

app.use(createBootstrap());
app.use(JsonViewer);

app.mount("#app");
