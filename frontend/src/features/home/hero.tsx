import { useI18n } from "@/i18n/i18n-provider";
import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";
import { assets } from "@/config/assets";
import { BackgroundCarousel } from "@/features/gallery/background-carousel";
import { LikeButton } from "./like-button";
export function Hero() {
  const { t } = useI18n();

  return (
    <section className="relative flex min-h-[720px] items-start overflow-hidden bg-background pb-16 pt-32 md:pt-36 md:min-h-[830px] md:pb-20">
      <BackgroundCarousel
        fallback={assets.hero}
        imageClassName="object-[center_60%]"
        fallbackImageClassName="md:translate-x-[8%]"
        priority
      />
      <div className="hero-scrim absolute inset-0" />
      <div className="texture absolute inset-0 opacity-30" />
      <div className="site-container relative z-10">
        <div className="min-w-0">
          <div className="mb-5 flex items-center gap-4">
            <span className="h-0.5 w-8 bg-primary" />
            <p className="eyebrow text-copper">巴黎华人联合足球俱乐部</p>
          </div>
          <h1 className="display max-w-3xl text-[clamp(4.5rem,10vw,9rem)]">
            <span className="block">Paris</span>
            <span className="block text-primary">Chinois</span>
            <span className="block">
              FC<span className="text-copper">.</span>
            </span>
          </h1>
          <div className="mt-6 flex max-w-xl flex-col items-start gap-5">
            <div className="flex gap-3">
              <Link
                to="/league"
                className="inline-flex h-12 items-center gap-3 bg-primary px-5 text-xs font-bold uppercase tracking-wider transition-colors hover:bg-oxblood"
              >
                {t("Fixtures")}
                <ArrowUpRight size={17} />
              </Link>
              <Link
                to="/team"
                className="inline-flex h-12 items-center gap-3 border border-foreground/45 px-5 text-xs font-bold uppercase tracking-wider transition-colors hover:bg-secondary"
              >
                {t("The squad")}
                <ArrowUpRight size={17} />
              </Link>
            </div>
            <LikeButton />
          </div>
        </div>
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-primary" />
    </section>
  );
}
