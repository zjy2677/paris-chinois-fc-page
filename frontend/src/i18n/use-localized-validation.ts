import { useEffect, useRef, type FormEvent } from "react";
import { useI18n } from "./i18n-provider";

export function useLocalizedValidation() {
  const { language, t } = useI18n();
  const ref = useRef<HTMLFormElement>(null);
  useEffect(() => {
    ref.current?.querySelectorAll("input, select, textarea").forEach((element) => {
      (element as HTMLInputElement).setCustomValidity("");
    });
  }, [language]);
  function onInvalid(event: FormEvent<HTMLFormElement>) {
    const field = event.target as HTMLInputElement;
    field.setCustomValidity("");
    if (field.validity.valueMissing) field.setCustomValidity(t("Please fill in this field."));
    else if (field.validity.typeMismatch)
      field.setCustomValidity(t("Please enter a valid email address."));
    else if (field.validity.tooShort)
      field.setCustomValidity(
        t("Please enter at least {count} characters.", { count: field.minLength }),
      );
  }
  function onInput(event: FormEvent<HTMLFormElement>) {
    (event.target as HTMLInputElement).setCustomValidity("");
  }
  return { ref, onInvalid, onInput };
}
