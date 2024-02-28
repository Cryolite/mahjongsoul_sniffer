<template>
  <div>
    <json-viewer v-show="visible" :value="jasonified" />
    <json-viewer v-show="visible && debugMode" :value="data" />
  </div>
</template>

<script>
import { JsonViewer } from "vue3-json-viewer";
import "vue3-json-viewer/dist/index.css";

export default {
  name: "ApiCallDetailView",

  components: {
    JsonViewer,
  },

  props: {
    data: {
      type: Object,
      required: true,
    },
    debugMode: Boolean,
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
          "double",
          "float",
          "int32",
          "int64",
          "uint32",
          "uint64",
          "sint32",
          "sint64",
          "fixed32",
          "fixed64",
          "sfixed32",
          "sfixed64",
          "bool",
          "string",
          "bytes",
        ];

        let result = {};
        for (const p in data) {
          const field = data[p];
          const wrapped = field.wrapped;
          const type = field.type;
          const value = field.value;
          const repeated = Array.isArray(value);
          const pp =
            p +
            " (" +
            type +
            (wrapped ? ", wrapped" : "") +
            (repeated ? ", repeated" : "") +
            ")";

          if (scalarValueTypes.includes(type)) {
            result[pp] = value;
            continue;
          }

          if (repeated) {
            result[pp] = value.map((e) => parse(e));
          } else {
            result[pp] = parse(value);
          }
        }

        return result;
      }

      return parse(this.data.value);
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped></style>
