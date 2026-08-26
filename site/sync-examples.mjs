#!/usr/bin/env node
// Sync the public download files from the source-of-truth in
// ../../assets/example/ into ./public/examples/, so that
// `astro build` (via `prebuild`) picks up the latest PDFs/DOCX/JSONs.
//
// Run manually with `npm run sync`. Auto-runs before every build.
import { copyFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, "..");
const srcDir = resolve(repoRoot, "assets/example");
const dstDir = resolve(__dirname, "public/examples");

mkdirSync(dstDir, { recursive: true });

const locales = ["zh", "en"];
const extensions = ["pdf", "docx", "json"];

let copied = 0;
let missing = 0;

for (const locale of locales) {
  for (const ext of extensions) {
    const src = resolve(srcDir, `example_resume_${locale}.${ext}`);
    const dst = resolve(dstDir, `${locale}.${ext}`);
    if (existsSync(src)) {
      copyFileSync(src, dst);
      copied++;
    } else {
      console.warn(`[sync] missing source: ${src}`);
      missing++;
    }
  }
}

console.log(`[sync] copied ${copied} file(s) to public/examples/${missing ? ` (${missing} skipped)` : ""}`);