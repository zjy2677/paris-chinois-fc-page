import { assets } from "@/config/assets";
import { useI18n } from "@/i18n/i18n-provider";
import { PageIntro } from "@/components/layout/page-intro";
import { ContactForm } from "./contact-form";
export function ContactPage() {
  const { t } = useI18n();
  return (
    <>
      <PageIntro
        backgroundImage={assets.contact}
        title={t("Contact")}
        description={t("Want to connect with the club? Leave a note here.")}
      />
      <section className="site-container grid gap-16 py-20 lg:grid-cols-[1.2fr_.8fr] lg:gap-28 lg:py-28">
        <div>
          <p className="eyebrow text-primary">{t("Your message")}</p>
          <h2 className="mt-4 font-display text-5xl font-bold uppercase">
            {t("Start a conversation.")}
          </h2>
          <div className="mt-10">
            <ContactForm />
          </div>
        </div>
        <aside className="space-y-10 border-t border-border pt-8 lg:border-t-0 lg:border-l lg:pl-16 lg:pt-0">
          <div>
            <p className="eyebrow text-copper">{t("Find us")}</p>
            <p className="mt-2 text-sm text-muted-foreground">
              {t("Confirm the training venue with the club before visiting.")}
            </p>
          </div>
          <div>
            <p className="eyebrow text-copper">{t("Social")}</p>
            <p className="mt-3 text-sm text-muted-foreground">
              {t("Official social links coming soon.")}
            </p>
          </div>
        </aside>
      </section>
    </>
  );
}
