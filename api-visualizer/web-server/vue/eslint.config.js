import { FlatCompat } from "@eslint/eslintrc";
import js from "@eslint/js";
import eslintConfigPrettier from "eslint-config-prettier";
import globals from "globals";

const compat = new FlatCompat();

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
  ...compat.extends("plugin:vue/vue3-recommended"),
  eslintConfigPrettier,
  {
    rules: {},
  },
];
