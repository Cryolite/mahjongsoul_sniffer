<template>
<div>
  <table>
    <tr>
      <td v-for="screenshot in screenshots" :key="screenshot.name">
        <a :href="screenshot.path"><img :src="screenshot.path" width="100" height="75"/></a>
      </td>
    </tr>
  </table>
  <textarea v-model="sniffer_log" rows="51" style="width: 50%;" readonly wrap="off"></textarea>
</div>
</template>

<script>
export default {
  data: function() {
    return {
      screenshots: [],
      sniffer_log: ""
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
      sniffer_log_xhr.open("GET", "/sniffer.log?n=50");
      sniffer_log_xhr.send();
    }, 1000);
  }
}
</script>
