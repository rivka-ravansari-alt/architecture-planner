const PLATFORM_OPTIONS = [
  { value: "web", label: "Web" },
  { value: "mobile", label: "Mobile" },
];

/**
 * Application platform selector (Web / Mobile).
 * @param {{ value: "web"|"mobile", onChange: (value: string) => void }} props
 */
export default function PlatformSelector({ value, onChange }) {
  return (
    <div className="field">
      <label>Application platform</label>
      <div className="chips" role="radiogroup" aria-label="Application platform">
        {PLATFORM_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={value === option.value}
            className={`chip${value === option.value ? " selected" : ""}`}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
