import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { translations, type Language, type TranslationKey } from "./translations";

const STORAGE_KEY = "paris-chinois-language";
import { translate, localizedDate, locales, type Parameters } from "./format";

type I18nContextValue = {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: TranslationKey, parameters?: Parameters) => string;
  c: (source: string) => string;
  formatDate: (date: string, options: Intl.DateTimeFormatOptions) => string;
};
const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({
  children,
  initialLanguage = "en",
}: {
  children: ReactNode;
  initialLanguage?: Language;
}) {
  // Match server output on the first client render, then restore the preference.
  const [language, setLanguageState] = useState<Language>(initialLanguage);
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "en" || saved === "fr" || saved === "zh") setLanguageState(saved);
    } catch {
      /* Storage can be disabled; the selector still works for this visit. */
    }
  }, []);
  const setLanguage = useCallback((next: Language) => {
    setLanguageState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* Keep in-memory preference. */
    }
  }, []);
  const t = useCallback(
    (key: TranslationKey, parameters?: Parameters) => translate(language, key, parameters),
    [language],
  );
  // Mock editorial records keep stable English source IDs; unknown future API copy passes through.
  const c = useCallback(
    (source: string) =>
      Object.hasOwn(translations.en, source) ? t(source as TranslationKey) : source,
    [t],
  );
  const formatDate = useCallback(
    (date: string, options: Intl.DateTimeFormatOptions) => localizedDate(language, date, options),
    [language],
  );
  useEffect(() => {
    document.documentElement.lang = locales[language];
  }, [language]);
  const value = useMemo(
    () => ({ language, setLanguage, t, c, formatDate }),
    [language, setLanguage, t, c, formatDate],
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const value = useContext(I18nContext);
  if (!value) throw new Error("useI18n must be used inside I18nProvider");
  return value;
}
