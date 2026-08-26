// Shared shape for both locales. Each component pulls only what it needs.

export type Locale = "zh" | "en";

export interface NavCopy {
  features: string;
  workflow: string;
  examples: string;
  locales: string;
  /** Other-locale label for the language switcher. */
  switchTo: { code: Locale; label: string };
}

export interface HeroCopy {
  eyebrow: string;
  /** Up to ~6 words / ~12 Chinese characters. Two lines max on desktop. */
  headline: string;
  /** ≤ 20 words / ≤ 60 Chinese characters. */
  subtext: string;
  ctaPrimary: string;
  ctaSecondary: string;
  /** Caption under the preview card. */
  previewCaption: string;
  /** Which preview asset to render. */
  previewImage: "zh" | "en";
}

export interface FeatureItem {
  title: string;
  body: string;
}

export interface FeaturesCopy {
  eyebrow: string;
  heading: string;
  body: string;
  items: [FeatureItem, FeatureItem, FeatureItem];
  jsonLabel: string;
  jsonLines: string;
  terminalLabel: string;
  terminalCmd: string;
  skillLabel: string;
  skillContext: string;
}

export interface WorkflowCopy {
  heading: string;
  body: string;
  cells: {
    write: { title: string; body: string };
    validate: { title: string; checks: string[] };
    render: { title: string; body: string };
    export: { title: string; body: string };
  };
  pipeline: string[];
  exportDocxSize: string;
  exportPdfSize: string;
}

export interface ShowcaseCopy {
  eyebrow: string;
  heading: string;
  body: string;
  caption: string;
  image: "zh" | "en";
  altText: string;
}

export interface LocaleItem {
  code: string;
  /** Single representative glyph for the locale tile. */
  glyph: string;
  name: string;
  page: string;
  note: string;
}

export interface LocalesCopy {
  heading: string;
  body: string;
  list: LocaleItem[];
}

export interface FooterCopy {
  heading: string;
  body: string;
  meta: {
    license: string;
    licenseValue: string;
    runtime: string;
    runtimeValue: string;
    locales: string;
    localesValue: string;
    output: string;
    outputValue: string;
  };
  copyright: string;
  ctaPrimary: string;
  ctaSecondary: string;
  navLinks: { features: string; workflow: string; examples: string; locales: string; source: string };
}

export interface I18nContent {
  code: Locale;
  htmlLang: string;
  siteTitle: string;
  siteDescription: string;
  nav: NavCopy;
  hero: HeroCopy;
  features: FeaturesCopy;
  workflow: WorkflowCopy;
  showcase: ShowcaseCopy;
  locales: LocalesCopy;
  footer: FooterCopy;
}