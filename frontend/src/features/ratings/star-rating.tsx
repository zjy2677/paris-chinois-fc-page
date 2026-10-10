import { Star } from "lucide-react";

export function StarRating({
  value,
  label,
  onChange,
}: {
  value: number | null;
  label: string;
  onChange?: (value: number) => void;
}) {
  if (onChange) {
    return (
      <div role="group" aria-label={label} className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            aria-label={`${star} / 5`}
            aria-pressed={value === star}
            onClick={() => onChange(star)}
            className="rounded p-1 text-copper transition hover:scale-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-copper"
          >
            <Star size={28} fill={value !== null && star <= value ? "currentColor" : "none"} />
          </button>
        ))}
      </div>
    );
  }
  return (
    <span role="img" className="inline-flex items-center gap-1 text-copper" aria-label={label}>
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          size={18}
          aria-hidden="true"
          fill={value !== null && star <= Math.round(value) ? "currentColor" : "none"}
        />
      ))}
    </span>
  );
}
