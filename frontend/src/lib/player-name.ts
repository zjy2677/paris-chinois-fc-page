import type { Language } from "@/i18n/translations";

export function localizedPlayerName(
  englishName: string,
  chineseName: string | null | undefined,
  language: Language,
): string {
  // Keep legacy players readable until an admin adds their Chinese name.
  return language === "zh" ? chineseName?.trim() || englishName : englishName;
}
