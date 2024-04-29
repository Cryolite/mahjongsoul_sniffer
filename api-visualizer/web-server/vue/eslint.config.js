import pluginVue from "eslint-plugin-vue";
import js from "@eslint/js";
import eslintConfigPrettier from "eslint-config-prettier";
import globals from "globals";

export default [
  {
    files: ["**/*.js", "**/*.vue"],
    ignores: ["**/dist/**/*", "**/node_modules/**/*"],
    languageOptions: {
      globals: {
        ...globals.node,
        ...globals.es2021,
      },
      parserOptions: {
        sourceType: "module",
        ecmaVersion: 2021,
      },
    },
  },
  js.configs.recommended,
  ...pluginVue.configs["flat/recommended"],
  eslintConfigPrettier,
  {
    rules: {},
  },
];
