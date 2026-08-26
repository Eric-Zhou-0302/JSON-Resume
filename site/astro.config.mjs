// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

// GitHub Pages project site.
// Final URL: https://Eric-Zhou-0302.github.io/JSON-Resume/
const SITE = "https://Eric-Zhou-0302.github.io";
const BASE = "/JSON-Resume";

export default defineConfig({
  site: SITE,
  base: BASE,
  trailingSlash: "ignore",
  build: {
    assets: "_assets",
    inlineStylesheets: "auto",
  },
  vite: {
    plugins: [tailwindcss()],
  },
  compressHTML: true,
});