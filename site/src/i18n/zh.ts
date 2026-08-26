import type { I18nContent } from "./types";

export const zh: I18nContent = {
  code: "zh",
  htmlLang: "zh-CN",
  siteTitle: "JSON-Resume：一份 JSON。一份简历。",
  siteDescription:
    "把简历写成一份严格的 JSON，生成器负责 Word 样式、项目符号、版式与链接，最后得到一份克制风格的 DOCX/PDF 简历。",

  nav: {
    features: "功能",
    workflow: "流程",
    examples: "示例",
    locales: "语言",
    switchTo: { code: "en", label: "English" },
  },

  hero: {
    eyebrow: "Python / DOCX + PDF",
    headline: "一份 JSON。\n一份简历。",
    subtext:
      "把简历写成 JSON，一行命令输出精致的 DOCX 或 PDF。Locale、排版、样式全部内置。",
    ctaPrimary: "在 GitHub 查看",
    ctaSecondary: "查看示例",
    previewCaption: "中文简历，A4，单页",
    previewImage: "zh",
  },

  features: {
    eyebrow: "你会得到",
    heading: "单一数据源。三种具体产物。",
    body: "再也不用跟 Word 样式搏斗。改一份 JSON，跑一条命令，简历每次都长一样。",
    items: [
      {
        title: "JSON 是唯一数据源",
        body: "在 Git 里版本化简历，在 PR 里 diff。同一份 JSON 渲染成 DOCX、PDF 或未来任意格式，不用复制粘贴，不用担心样式崩坏。",
      },
      {
        title: "一行命令同时出 DOCX 和 PDF",
        body: "生成真正带样式、项目符号、链接的 Word 文件。加 --pdf 参数，在同一次运行里一并导出 PDF。",
      },
      {
        title: "为 AI Agent 而生",
        body: "仓库自带一流的 SKILL.md。Codex、Claude Code、WorkBuddy 都能直接编写或修改简历 JSON、校验、渲染，无需定制胶水代码。",
      },
    ],
    jsonLabel: "resume.json",
    jsonLines: "42 行",
    terminalLabel: "终端",
    terminalCmd: "python main.py",
    skillLabel: "SKILL.md",
    skillContext: "前置元数据",
  },

  workflow: {
    heading: "一条管线。没有魔术。",
    body: "每一步都是 resume_generator/ 里一个真实的 Python 函数。整个流程装得下你的脑子。",
    cells: {
      write: {
        title: "书写",
        body: "亲手写，或者让 Agent 写一份 JSON。没有模板，没有合并域，没有 Word 插件。",
      },
      validate: {
        title: "校验",
        checks: [
          "locale 必须是 zh-CN、en-US、en-GB 或 en-EU",
          "name.full 与 contact.email 必须存在",
          "section.title 不能为空",
          "entry 的日期字符串可以解析",
        ],
      },
      render: {
        title: "渲染",
        body: "解析为带类型的模型，然后从一张空白的 .docx 文档开始构建 Word 文件。",
      },
      export: {
        title: "导出",
        body: "一次运行产出两个文件。内容、排版、链接完全一致。",
      },
    },
    pipeline: ["JSON", "姓名", "联系方式", "条目", "章节", "DOCX"],
    exportDocxSize: "38 KB",
    exportPdfSize: "112 KB",
  },

  showcase: {
    eyebrow: "输出",
    heading: "真 Word。真 PDF。一页搞定。",
    body: "一份渲染好的中文简历，A4 单页。稳定的排版、真实的 Word 编号、真正可点击的超链接。DOCX 和 PDF 内容完全一致。",
    caption: "中文简历，A4，单页",
    image: "zh",
    altText: "渲染好的中文简历预览，A4 单页，由 JSON 生成",
  },

  locales: {
    heading: "Locale 严格，按页适配",
    body: "顶层 locale 字段必填且严格。它决定纸张尺寸、字体，以及资深招聘官一眼看到的小细节。",
    list: [
      {
        code: "zh-CN",
        glyph: "简",
        name: "中文（简体）",
        page: "A4",
        note: "东亚字体，显式 w:eastAsia",
      },
      {
        code: "en-US",
        glyph: "Aa",
        name: "英文（美国）",
        page: "Letter",
        note: "8.5 × 11 英寸",
      },
      {
        code: "en-GB",
        glyph: "Aa",
        name: "英文（英国）",
        page: "A4",
        note: "按章节区分英式拼写",
      },
      {
        code: "en-EU",
        glyph: "Aa",
        name: "英文（欧盟）",
        page: "A4",
        note: "欧式标点",
      },
    ],
  },

  footer: {
    heading: "点 Star，跑你的简历。",
    body: "一份 JSON、一条命令、一页纸。MIT 协议开源。",
    meta: {
      license: "协议",
      licenseValue: "MIT",
      runtime: "运行时",
      runtimeValue: "Python 3.11",
      locales: "支持语言",
      localesValue: "zh-CN、en-US、en-GB、en-EU",
      output: "输出格式",
      outputValue: "DOCX、PDF",
    },
    copyright: "© Eric Zhou. MIT 协议开源。",
    ctaPrimary: "在 GitHub 查看",
    ctaSecondary: "阅读 SKILL.md",
    navLinks: {
      features: "功能",
      workflow: "流程",
      examples: "示例",
      locales: "语言",
      source: "源码",
    },
  },
};