type SearchPillProps = {
  value: string;
  onChange: (value: string) => void;
};

export function SearchPill({ value, onChange }: SearchPillProps) {
  return (
    <label className="ltc-search">
      <svg
        width={13}
        height={13}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2.75}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden
      >
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
      </svg>
      <input
        type="search"
        className="ltc-search-input"
        placeholder="Search runs…"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label="Search runs"
      />
    </label>
  );
}
