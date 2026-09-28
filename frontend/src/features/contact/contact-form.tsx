import { useLocalizedValidation } from "@/i18n/use-localized-validation";
import { useI18n } from "@/i18n/i18n-provider";
import { useState } from "react";
import { Button } from "@/components/ui/button";
export function ContactForm() {
  const { t } = useI18n();
  const validation = useLocalizedValidation();
  const [sent, setSent] = useState(false);
  return (
    <form
      {...validation}
      className="space-y-6"
      onSubmit={(e) => {
        e.preventDefault();
        setSent(true);
      }}
    >
      <div className="grid gap-6 sm:grid-cols-2">
        <label className="block text-sm font-medium">
          {t("Your name")}
          <input
            required
            minLength={2}
            name="name"
            autoComplete="name"
            className="mt-2 h-12 w-full border border-border bg-card px-4 outline-none focus:border-copper"
            placeholder={t("Your name")}
          />
        </label>
        <label className="block text-sm font-medium">
          {t("Email address")}
          <input
            required
            type="email"
            name="email"
            autoComplete="email"
            className="mt-2 h-12 w-full border border-border bg-card px-4 outline-none focus:border-copper"
            placeholder="you@example.com"
          />
        </label>
      </div>
      <label className="block text-sm font-medium">
        {t("Subject")}
        <select
          name="subject"
          required
          defaultValue=""
          className="mt-2 h-12 w-full border border-border bg-card px-4 outline-none focus:border-copper"
        >
          <option value="" disabled>
            {t("Choose a subject")}
          </option>
          <option value="general">{t("General enquiry")}</option>
          <option value="join">{t("Join the club")}</option>
          <option value="media">{t("Media")}</option>
          <option value="other">{t("Other")}</option>
        </select>
      </label>
      <label className="block text-sm font-medium">
        {t("Message")}
        <textarea
          required
          minLength={10}
          name="message"
          rows={6}
          className="mt-2 w-full resize-y border border-border bg-card p-4 outline-none focus:border-copper"
          placeholder={t("Tell us what’s on your mind...")}
        />
      </label>
      <Button
        type="submit"
        className="h-12 rounded-none bg-primary px-8 text-xs font-bold uppercase tracking-widest text-foreground hover:bg-oxblood"
      >
        {t("Send message")}
      </Button>
      {sent && (
        <p role="status" className="border-l-2 border-copper pl-4 text-sm text-copper">
          {t("Message submission is currently unavailable. Your message has not been sent.")}
        </p>
      )}
    </form>
  );
}
