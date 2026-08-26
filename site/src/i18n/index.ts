import type { Locale, I18nContent } from "./types";
import { zh } from "./zh";
import { en } from "./en";

export type { Locale, I18nContent } from "./types";

const all: Record<Locale, I18nContent> = { zh, en };

export function getContent(locale: Locale): I18nContent {
  return all[locale];
}

export function getOtherLocale(locale: Locale): Locale {
  return locale === "zh" ? "en" : "zh";
}

/**
 * URL that points to the same page in the other locale.
 * The Astro `base` (configured for GitHub Pages) is baked in at build time.
 */
export function otherLocaleHref(locale: Locale): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, "");
  // Default site is Chinese (/); English lives under /en/.
  const target = locale === "zh" ? `${base}/en/` : `${base}/`;
  return target;
}