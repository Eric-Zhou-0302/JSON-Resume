import type { I18nContent } from "./types";

export const en: I18nContent = {
  code: "en",
  htmlLang: "en",
  siteTitle: "JSON-Resume: One JSON. One Resume.",
  siteDescription:
    "Write your resume as a single JSON file. JSON-Resume renders a polished DOCX or PDF in one command, with locale, layout, and styling baked in.",

  nav: {
    features: "Features",
    workflow: "Workflow",
    examples: "Examples",
    locales: "Locales",
    switchTo: { code: "zh", label: "中文" },
  },

  hero: {
    eyebrow: "Python / DOCX + PDF",
    headline: "One JSON.\nOne Resume.",
    subtext:
      "Write your resume as JSON. Render a polished DOCX or PDF in one command, with locale and styling baked in.",
    ctaPrimary: "View on GitHub",
    ctaSecondary: "View Example",
    previewCaption: "en-US, Letter, single page",
    previewImage: "en",
  },

  features: {
    eyebrow: "What you get",
    heading: "One source of truth. Three concrete outputs.",
    body: "No more fighting Word styles. Edit a JSON file, run one command, get a resume that looks the same every time.",
    items: [
      {
        title: "JSON as the source of truth",
        body: "Version your resume in Git. Diff it in PRs. Render the same JSON to DOCX, PDF, or a future format, with no copy-paste and no broken styles.",
      },
      {
        title: "DOCX and PDF, one command",
        body: "Generate a real Word file with styles, lists, and links baked in. Add --pdf to export the same content to PDF in the same run.",
      },
      {
        title: "Built for AI Agents",
        body: "A first-class SKILL.md ships in the repo. Codex, Claude Code, and WorkBuddy can author or edit a resume JSON, validate it, and render it without bespoke glue code.",
      },
    ],
    jsonLabel: "resume.json",
    jsonLines: "42 lines",
    terminalLabel: "Terminal",
    terminalCmd: "python main.py",
    skillLabel: "SKILL.md",
    skillContext: "frontmatter",
  },

  workflow: {
    heading: "One pipeline. No magic.",
    body: "Each step is a real Python function in resume_generator/. The whole thing fits in your head.",
    cells: {
      write: {
        title: "Write",
        body: "Hand-author or have an agent author a single JSON file. No templates, no merge fields, no Word add-ins.",
      },
      validate: {
        title: "Validate",
        checks: [
          "locale is one of zh-CN, en-US, en-GB, en-EU",
          "name.full and contact.email are present",
          "section.title is non-empty",
          "entry date strings parse",
        ],
      },
      render: {
        title: "Render",
        body: "Parse to typed models, then build a Word document from a blank .docx.",
      },
      export: {
        title: "Export",
        body: "One run produces both files. Same content, same layout, same links.",
      },
    },
    pipeline: ["JSON", "Name", "Contact", "Entry", "Section", "DOCX"],
    exportDocxSize: "38 KB",
    exportPdfSize: "112 KB",
  },

  showcase: {
    eyebrow: "Output",
    heading: "Real Word. Real PDF. One page.",
    body: "A rendered English resume at Letter, single page. Stable typography, real Word numbering, working hyperlinks. The same content lands on the page whether you open the DOCX or the PDF.",
    caption: "en-US, Letter, single page",
    image: "en",
    altText:
      "Rendered English resume preview, Letter single page, generated from a JSON file",
  },

  locales: {
    heading: "Locale aware, page by page",
    body: "The top-level locale field is required and strict. It picks the page size, the fonts, and the small punctuation differences that show up under a recruiter's eye.",
    list: [
      {
        code: "zh-CN",
        glyph: "简",
        name: "Chinese (Simplified)",
        page: "A4",
        note: "East Asian font, explicit w:eastAsia",
      },
      {
        code: "en-US",
        glyph: "Aa",
        name: "English (US)",
        page: "Letter",
        note: "8.5 x 11 in",
      },
      {
        code: "en-GB",
        glyph: "Aa",
        name: "English (UK)",
        page: "A4",
        note: "British spelling by section",
      },
      {
        code: "en-EU",
        glyph: "Aa",
        name: "English (EU)",
        page: "A4",
        note: "European punctuation",
      },
    ],
  },

  footer: {
    heading: "Star the repo, render your resume.",
    body: "One JSON, one command, one page. Open source under the MIT license.",
    meta: {
      license: "License",
      licenseValue: "MIT",
      runtime: "Runtime",
      runtimeValue: "Python 3.11",
      locales: "Locales",
      localesValue: "zh-CN, en-US, en-GB, en-EU",
      output: "Output",
      outputValue: "DOCX, PDF",
    },
    copyright: "\u00a9 Eric Zhou. Released under the MIT License.",
    ctaPrimary: "View on GitHub",
    ctaSecondary: "Read SKILL.md",
    navLinks: {
      features: "Features",
      workflow: "Workflow",
      examples: "Examples",
      locales: "Locales",
      source: "Source",
    },
  },
};