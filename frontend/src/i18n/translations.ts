import { en } from "./locales/en";
import { fr } from "./locales/fr";
import { zh } from "./locales/zh";
export type Language = "en" | "fr" | "zh";
export type TranslationKey = keyof typeof en;
export type Messages = Record<TranslationKey, string>;
export const translations: Record<Language, Messages> = { en, fr, zh };
export const languageOptions: Array<{ code: Language; label: string; name: string }> = [
  { code: "en", label: "EN", name: "English" },
  { code: "fr", label: "FR", name: "Français" },
  { code: "zh", label: "中文", name: "中文" },
];
