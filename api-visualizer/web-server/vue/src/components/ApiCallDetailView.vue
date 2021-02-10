<template>
  <div>
    <json-viewer :value="jasonified" v-show="visible"/>
    <json-viewer :value="data" v-show="visible && debugMode"/>
  </div>
</template>

<script>
import JsonViewer from 'vue-json-viewer'

export default {
  name: 'ApiCallDetailView',

  components: {
    JsonViewer
  },

  props: {
    data: Object,
    debugMode: Boolean
  },

  computed: {
    visible() {
      return this.data !== null;
    },

    jasonified() {
      if (this.data === null) {
        return {};
      }

      function parse(data) {
        const scalarValueTypes = [
          "double", "float", "int32", "int64", "uint32", "uint64", "sint32",
          "sint64", "fixed32", "fixed64", "sfixed32", "sfixed64", "bool",
          "string", "bytes"
        ];

        let result = {};
        for (const p in data) {
          const field = data[p];
          const wrapped = field.wrapped;
          const type = field.type;
          const value = field.value;
          const repeated = Array.isArray(value);
          const pp = p + " (" + type + (wrapped ? ", wrapped" : "") + (repeated ? ", repeated" : "") + ")";

          if (scalarValueTypes.includes(type)) {
            result[pp] = value;
            continue;
          }

          if (repeated) {
            result[pp] = value.map(e => parse(e));
          }
          else {
            result[pp] = parse(value);
          }
        }

        return result;
      }

      return parse(this.data.value);
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
