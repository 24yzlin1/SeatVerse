import js from "@eslint/js";
import eslintConfigPrettier from "eslint-config-prettier";
import svelte from "eslint-plugin-svelte";
import globals from "globals";
import tseslint from "typescript-eslint";
import svelteConfig from "./svelte.config.js";

export default [
  // shadcn generated files follow the project convention: excluded from
  // hand-written code rules and never edited manually.
  {
    ignores: [
      "node_modules/**",
      "dist/**",
      "public/**",
      "src/lib/components/ui/**",
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...svelte.configs.recommended,
  ...svelte.configs.prettier,
  {
    files: ["**/*.svelte", "**/*.svelte.ts", "**/*.svelte.js"],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
        extraFileExtensions: [".svelte"],
        svelteConfig,
      },
    },
  },
  {
    files: ["**/*.{js,ts,svelte}"],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      // Strict mode: any non-conforming style is reported as error.
      curly: ["error", "all"],
      eqeqeq: ["error", "always"],
      "no-var": "error",
      // destructuring: "all" -- when at least one member of a Svelte
      // `let { ... } = $props()` is written via bind: or $bindable, the
      // whole declaration must stay let. Report only when every
      // destructured member is never reassigned, to avoid false positives.
      "prefer-const": ["error", { destructuring: "all" }],
      "no-else-return": "error",
      "no-lonely-if": "error",
      "no-unneeded-ternary": "error",
      "no-useless-return": "error",
      "no-implicit-coercion": "error",
      "object-shorthand": "error",
      "prefer-template": "error",
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/consistent-type-imports": "error",
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
  eslintConfigPrettier,
  {
    // eslint-config-prettier disables curly, so re-enable it after that:
    // if / else / for / while blocks must never omit braces.
    files: ["**/*.{js,ts,svelte}"],
    rules: {
      curly: ["error", "all"],
    },
  },
];
