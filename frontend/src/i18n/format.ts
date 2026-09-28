import { translations, type Language, type TranslationKey } from "./translations";

export const locales: Record<Language, string> = { en: "en-GB", fr: "fr-FR", zh: "zh-CN" };
export type Parameters = Record<string, string | number>;

export function translate(language: Language, key: TranslationKey, parameters: Parameters = {}) {
  return translations[language][key].replace(/\{(\w+)\}/g, (token, name: string) =>
    String(parameters[name] ?? token),
  );
}

export function localizedDate(
  language: Language,
  value: string,
  options: Intl.DateTimeFormatOptions,
) {
  // Date-only news records are calendar dates, independent of the viewer's timezone.
  const date = new Date(value.length === 10 ? `${value}T12:00:00Z` : value);
  return new Intl.DateTimeFormat(locales[language], {
    ...options,
    timeZone: "Europe/Paris",
  }).format(date);
}
