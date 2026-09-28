import type { TranslationKey } from "@/i18n/translations";

// Club history and honours supplied by the club; years are shared across locales.
export const honours: Array<{ name: TranslationKey; years: number[] }> = [
  { name: "about.cupLyon", years: [2014, 2015, 2018, 2019, 2022, 2024, 2025] },
  { name: "about.cupStuttgart", years: [2016] },
  { name: "about.cupEurope", years: [2016, 2017] },
  { name: "about.cupPampas", years: [2016, 2017, 2018] },
  { name: "about.cupParis", years: [2023] },
  { name: "about.cupMunich", years: [2023] },
];
