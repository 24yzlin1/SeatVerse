import { Buffer } from "node:buffer";
import { readFile } from "node:fs/promises";
import { URL } from "node:url";
import ts from "typescript";

const modules = new Map();

async function moduleUrl(url) {
  if (modules.has(url.href)) return modules.get(url.href);
  const source = await readFile(url, "utf8");
  let { outputText } = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2023,
    },
  });
  for (const match of [...outputText.matchAll(/from "([^"]+)"/g)]) {
    const specifier = match[1];
    const dependency = specifier.startsWith(".")
      ? await moduleUrl(new URL(`${specifier.replace(/\.ts$/, "")}.ts`, url))
      : import.meta.resolve(specifier);
    outputText = outputText.replace(match[0], `from "${dependency}"`);
  }
  const result = `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`;
  modules.set(url.href, result);
  return result;
}

export async function loadTypeScript(url) {
  return import(await moduleUrl(url));
}
