import js from "@eslint/js";
import eslintConfigPrettier from "eslint-config-prettier";
import globals from "globals";
import svelte from "eslint-plugin-svelte";
import svelteParser from "svelte-eslint-parser";
import tseslint from "typescript-eslint";
import svelteConfig from "./svelte.config.js";

/** 手写代码统一遵守的通用风格规则 */
const sharedRules = {
  curly: ["error", "all"],
  eqeqeq: ["error", "always"],
  "no-var": "error",
  "prefer-const": "error",
  "no-else-return": "error",
  "no-lonely-if": "error",
  "no-unneeded-ternary": "error",
  "no-useless-return": "error",
  "no-implicit-coercion": "error",
  "object-shorthand": "error",
  "prefer-template": "error",
};

/** 项目规范：忽略注释一律禁止，含带说明的 @ts-expect-error */
const bannedTsComments = [
  "error",
  {
    "ts-expect-error": true,
    "ts-ignore": true,
    "ts-nocheck": true,
    "ts-check": false,
  },
];

export default [
  {
    // dist 为构建产物；components/ui 为 shadcn 生成件，禁止手改也不参与手写规则
    ignores: ["node_modules/**", "dist/**", "src/lib/components/ui/**"],
  },
  {
    // 未使用的 eslint-disable 注释也按错误处理，避免「先关再说」
    linterOptions: { reportUnusedDisableDirectives: "error" },
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...svelte.configs.recommended,
  {
    files: ["**/*.ts", "**/*.tsx"],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      ...sharedRules,
      "@typescript-eslint/ban-ts-comment": bannedTsComments,
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/consistent-type-imports": "error",
      "@typescript-eslint/no-namespace": ["error", { allowDeclarations: true }],
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          args: "after-used",
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
        },
      ],
    },
  },
  {
    files: ["**/*.svelte", "**/*.svelte.ts", "**/*.svelte.js"],
    languageOptions: {
      parser: svelteParser,
      parserOptions: {
        parser: tseslint.parser,
        extraFileExtensions: [".svelte"],
        svelteConfig,
      },
      globals: { ...globals.browser },
    },
    rules: {
      ...sharedRules,
      "@typescript-eslint/ban-ts-comment": bannedTsComments,
    },
  },
  eslintConfigPrettier,
];
