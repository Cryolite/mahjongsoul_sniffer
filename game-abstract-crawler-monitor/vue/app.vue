<template>
<div>
  <h1>MahjongSoul Game Abstract Crawler Monitor</h1>

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

  <h2>CRAWLER</h2>
  <textarea v-model="crawler_log" rows="30" style="width: 100%;" readonly wrap="off"></textarea>
</div>
</template>

<script>
export default {
  data: function() {
    return {
      screenshots: [],
      sniffer_log: "",
      archiver_log: ""
    };
  },

  created: function() {
    var vm = this;

    var screenshots_xhr = new XMLHttpRequest();
    screenshots_xhr.onreadystatechange = function() {
      if (this.readyState == XMLHttpRequest.DONE) {
        if (this.status == 200) {
          var screenshots = JSON.parse(this.responseText);
          for (var i = 0; i < screenshots.length; ++i) {
            var screenshot = screenshots[i];
            screenshot.path = "/screenshot/" + screenshot.name;
            vm.screenshots.push(screenshot);
          }
        }
      }
    };
    screenshots_xhr.open("GET", "/screenshots.json");
    screenshots_xhr.send();

    setInterval(function () {
      var sniffer_log_xhr = new XMLHttpRequest();
      sniffer_log_xhr.onreadystatechange = function() {
        if (this.readyState == XMLHttpRequest.DONE && this.status == 200) {
          vm.sniffer_log = this.responseText;
        }
      };
      sniffer_log_xhr.open("GET", "/sniffer.log");
      sniffer_log_xhr.send();
    }, 60000);

    setInterval(function () {
      var archiver_log_xhr = new XMLHttpRequest();
      archiver_log_xhr.onreadystatechange = function() {
        if (this.readyState == XMLHttpRequest.DONE && this.status == 200) {
          vm.archiver_log = this.responseText;
        }
      };
      archiver_log_xhr.open("GET", "/archiver.log");
      archiver_log_xhr.send();
    }, 60000);

    setInterval(function () {
      var crawler_log_xhr = new XMLHttpRequest();
      crawler_log_xhr.onreadystatechange = function() {
        if (this.readyState == XMLHttpRequest.DONE && this.status == 200) {
          vm.crawler_log = this.responseText;
        }
      };
      crawler_log_xhr.open("GET", "/crawler.log");
      crawler_log_xhr.send();
    }, 60000);
  }
}
</script>
