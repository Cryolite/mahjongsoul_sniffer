<template>
  <div>
    <table class="table table-sm table-striped table-borderless table-hover">
      <tbody>
        <tr v-for="data in dataList" :key="data.index" :class="itemClass(data)">
          <td class="px-1 py-0 shrink-to-fit">
            <a style="cursor: pointer" @click="deleteItem(data)">
              <img alt="delete" src="@/assets/x.svg" />
            </a>
          </td>
          <td class="px-1 py-0 shrink-to-fit">
            <a @click="setRequestAsDetailView(data)">
              <img alt="request" :src="requestImageSrc(data.value)" />
            </a>
          </td>
          <td class="px-1 py-0 shrink-to-fit">
            <a
              v-show="showResponseAnchor(data)"
              @click="setResponseAsDetailView(data)"
            >
              <img alt="response" :src="responseImageSrc(data.value)" />
            </a>
          </td>
          <td class="small shrink-to-fit">
            {{ getTimestamp(data.value) }}
          </td>
          <td class="small text-left">
            {{ data.value.name }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import uploadSvg from "@/assets/upload.svg";
import downloadSvg from "@/assets/download.svg";

const props = defineProps({
  setDetailView: {
    type: Function,
    required: true,
  },
});

const counter = ref(0);
const dataList = ref([]);
const detailViewIndex = ref(null);

const itemClass = (data) => {
  if (data.index == detailViewIndex.value) {
    return { "bg-secondary": true, "text-white": true };
  }
  return { "bg-secondary": false, "text-white": false };
};

const deleteItem = (data) => {
  const index = data.index;
  dataList.value = dataList.value.filter((data) => data.index != index);
  if (index == detailViewIndex.value) {
    props.setDetailView(null);
    detailViewIndex.value = null;
  }
};

const requestImageSrc = (data) => {
  return data.request_direction == "outbound" ? uploadSvg : downloadSvg;
};

const setRequestAsDetailView = (data) => {
  props.setDetailView(data.value.request);
  detailViewIndex.value = data.index;
};

const showResponseAnchor = (data) => {
  return data.value.response !== null;
};

const responseImageSrc = (data) => {
  return data.request_direction == "outbound" ? downloadSvg : uploadSvg;
};

const setResponseAsDetailView = (data) => {
  props.setDetailView(data.value.response);
  detailViewIndex.value = data.index;
};

const getTimestamp = (data) => {
  const timestamp = new Date(data.timestamp * 1000);
  const year = timestamp.getFullYear().toString();
  const month = timestamp.getMonth().toString().padStart(2, "0");
  const day = timestamp.getDate().toString().padStart(2, "0");
  const hours = timestamp.getHours().toString().padStart(2, "0");
  const minutes = timestamp.getMinutes().toString().padStart(2, "0");
  const seconds = timestamp.getSeconds().toString().padStart(2, "0");
  return (
    year + "/" + month + "/" + day + " " + hours + ":" + minutes + ":" + seconds
  );
};

onMounted(() => {
  setInterval(function () {
    const xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
      if (this.readyState == XMLHttpRequest.DONE && this.status == 200) {
        for (const data of JSON.parse(this.responseText)) {
          dataList.value.push({ index: counter.value++, value: data });
        }
      }
    };
    xhr.open("GET", "/api-calls.json");
    xhr.send();
  }, 1000);
});
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
td.shrink-to-fit {
  width: 1%;
  white-space: nowrap;
}

a {
  cursor: pointer;
}
</style>
