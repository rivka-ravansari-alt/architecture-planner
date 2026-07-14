const STAGE_OPTIONS = [
  { value: "mvp", label: "MVP" },
  { value: "production", label: "Production" },
];

/**
 * Stage selector (MVP / Production).
 * @param {{ value: "mvp"|"production", onChange: (value: string) => void }} props
 */
export default function StageSelector({ value, onChange }) {
  return (
    <div className="field">
      <label>Stage</label>
      <div className="chips" role="radiogroup" aria-label="Stage">
        {STAGE_OPTIONS.map((option) => (
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
