<template>
  <div>
    <table class="table table-sm table-striped table-borderless table-hover">
      <tbody>
        <tr v-for="data in dataList" :key="data.index" :class="itemClass(data)">
          <td class="px-1 py-0 shrink-to-fit">
            <a @click="deleteItem(data)" style="cursor: pointer;">
              <img alt="delete" src="@/assets/x.svg"/>
            </a>
          </td>
          <td class="px-1 py-0 shrink-to-fit">
            <a @click="setRequestAsDetailView(data)">
              <img alt="request" :src="requestImageSrc(data.value)"/>
            </a>
          </td>
          <td class="px-1 py-0 shrink-to-fit">
            <a @click="setResponseAsDetailView(data)" v-show="showResponseAnchor(data)">
              <img alt="response" :src="responseImageSrc(data.value)"/>
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

<script>
export default {
  name: 'ApiCallListView',

  props: {
    setDetailView: Function
  },

  data() {
    const self = this;

    return {
      counter: 0,

      dataList: [],

      itemClass(data) {
        if (data.index == self.detailViewIndex) {
          return { "bg-secondary": true, "text-white": true };
        }
        return { "bg-secondary": false, "text-white": false };
      },

      deleteItem(data) {
        const index = data.index;
        self.dataList = self.dataList.filter(data => data.index != index);
        if (index == self.detailViewIndex) {
          self.setDetailView(null);
          self.detailViewIndex = null;
        }
      },

      detailViewIndex: null,

      requestImageSrc(data) {
        return data.request_direction == "outbound"
          ? require("@/assets/upload.svg") : require("@/assets/download.svg");
      },

      setRequestAsDetailView(data) {
        self.setDetailView(data.value.request);
        self.detailViewIndex = data.index;
      },

      showResponseAnchor(data) {
        return data.value.response !== null;
      },

      responseImageSrc(data) {
        return data.request_direction == "outbound"
          ? require("@/assets/download.svg") : require("@/assets/upload.svg");
      },

      setResponseAsDetailView(data) {
        self.setDetailView(data.value.response);
        self.detailViewIndex = data.index;
      },

      getTimestamp(data) {
        const timestamp = new Date(data.timestamp * 1000);
        const year = timestamp.getFullYear().toString();
        const month = timestamp.getMonth().toString().padStart(2, '0');
        const day = timestamp.getDate().toString().padStart(2, '0');
        const hours = timestamp.getHours().toString().padStart(2, '0');
        const minutes = timestamp.getMinutes().toString().padStart(2, '0');
        const seconds = timestamp.getSeconds().toString().padStart(2, '0');
        return year + "/" + month + "/" + day + " " + hours + ":" + minutes + ":" + seconds;
      }
    }
  },

  created() {
    const vm = this;

    setInterval(function() {
      const xhr = new XMLHttpRequest();
      xhr.onreadystatechange = function() {
        if (this.readyState == XMLHttpRequest.DONE && this.status == 200) {
          for (const data of JSON.parse(this.responseText)) {
            vm.dataList.push({ index: vm.counter++, value: data });
          }
        }
      };
      xhr.open("GET", "/api-calls.json");
      xhr.send();
    }, 1000);
  }
}
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
