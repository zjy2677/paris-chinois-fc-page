import { useI18n } from "./i18n-provider";
import type { TranslationKey } from "./translations";

export function TranslatedText({ message }: { message: TranslationKey }) {
  const { t } = useI18n();
  return t(message);
}
