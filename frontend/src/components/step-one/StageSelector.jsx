const STAGE_OPTIONS = [
  { value: "mvp", label: "MVP" },
  { value: "production", label: "Production", disabled: true },
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
            aria-disabled={option.disabled || undefined}
            disabled={option.disabled}
            className={`chip${value === option.value ? " selected" : ""}${
              option.disabled ? " disabled" : ""
            }`}
            onClick={() => {
              if (!option.disabled) onChange(option.value);
            }}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
