type PageIntroProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  backgroundImage?: string;
};

export function PageIntro({ eyebrow, title, description, backgroundImage }: PageIntroProps) {
  return (
    <section className="relative overflow-hidden border-b border-border bg-card pt-44 pb-16 md:pt-52 md:pb-24">
      {backgroundImage && (
        <>
          <img
            src={backgroundImage}
            alt=""
            aria-hidden="true"
            fetchPriority="high"
            className="absolute inset-0 h-full w-full object-cover object-center"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-black/85 via-black/65 to-black/45" />
        </>
      )}
      <div className="texture absolute inset-0 opacity-40" />
      <div className="site-container relative">
        {eyebrow && <p className="eyebrow mb-5 text-copper">{eyebrow}</p>}
        <h1 className="section-title max-w-5xl">{title}</h1>
        {description && (
          <p
            className={`mt-7 max-w-xl text-base md:text-lg ${backgroundImage ? "text-white/85" : "text-muted-foreground"}`}
          >
            {description}
          </p>
        )}
      </div>
    </section>
  );
}
