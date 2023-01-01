<template>
<div>
  <h1>MahjongSoul Game Detail Crawler Monitor</h1>

  <h2>Screenshots</h2>
  <table>
    <tr>
      <td v-for="screenshot in screenshots" :key="screenshot.name">
        <a :href="screenshot.path"><img :src="screenshot.path" width="100" height="75"/></a>
      </td>
    </tr>
  </table>

  <h2>Sniffer</h2>
  <textarea v-model="sniffer_log" rows="30" style="width: 100%;" readonly wrap="off"></textarea>

  <h2>Archiver</h2>
  <textarea v-model="archiver_log" rows="30" style="width: 100%;" readonly wrap="off"></textarea>

  <h2>Crawler</h2>
  <textarea v-model="crawler_log" rows="30" style="width: 100%;" readonly wrap="off"></textarea>
</div>
</template>

<script>
export default {
  data: function() {
    return {
      screenshots: [],
      sniffer_log: "",
      archiver_log: "",
      crawler_log: ""
    };
  },

  created: function() {
    const vm = this;

    const screenshots_xhr = new XMLHttpRequest();
    screenshots_xhr.onreadystatechange = function() {
      if (this.readyState == XMLHttpRequest.DONE) {
        if (this.status == 200) {
          const screenshots = JSON.parse(this.responseText);
          for (let i = 0; i < screenshots.length; ++i) {
            const screenshot = screenshots[i];
            screenshot.path = "/screenshot/" + screenshot.name;
            vm.screenshots.push(screenshot);
          }
        }
      }
    };
    screenshots_xhr.open("GET", "/screenshots.json");
    screenshots_xhr.send();

    setInterval(function () {
      const log_xhr = new XMLHttpRequest();
      log_xhr.onreadystatechange = function() {
        if (this.readyState == XMLHttpRequest.DONE && this.status == 200) {
          const log = JSON.parse(this.responseText);
          vm.sniffer_log = log.sniffer.join("\n")
          vm.archiver_log = log.archiver.join("\n")
          vm.crawler_log = log.crawler.join("\n")
        }
      };
      log_xhr.open("GET", "/log.json");
      log_xhr.send();
    }, 10000);
  }
}
</script>
