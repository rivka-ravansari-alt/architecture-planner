/**
 * Renders a single conditional requirement field.
 * @param {{ field: object, value: any, error?: string, onChange: (value: any) => void }} props
 */
export default function RequirementField({ field, value, error, onChange }) {
  if (field.type === "checkbox_group") {
    const selected = Array.isArray(value) ? value : [];
    const toggle = (option) => {
      onChange(
        selected.includes(option)
          ? selected.filter((item) => item !== option)
          : [...selected, option]
      );
    };

    return (
      <div className="field">
        <label>{field.label}</label>
        <div className="option-group">
          {field.options.map((option) => (
            <label className="option-check" key={option.value}>
              <input
                type="checkbox"
                checked={selected.includes(option.value)}
                onChange={() => toggle(option.value)}
              />
              {option.label}
            </label>
          ))}
        </div>
      </div>
    );
  }

  if (field.type === "radio") {
    return (
      <div className="field">
        <label>{field.label}</label>
        <div className="option-group">
          {field.options.map((option) => (
            <label className="option-check" key={option.value}>
              <input
                type="radio"
                name={field.key}
                checked={value === option.value}
                onChange={() => onChange(option.value)}
              />
              {option.label}
            </label>
          ))}
        </div>
      </div>
    );
  }

  if (field.type === "select") {
    return (
      <div className="field">
        <label>{field.label}</label>
        <select
          value={value ?? ""}
          onChange={(event) => onChange(event.target.value)}
        >
          <option value="" disabled>
            Select an option
          </option>
          {field.options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    );
  }

  if (field.type === "number") {
    return (
      <div className="field">
        <label>{field.label}</label>
        <input
          type="number"
          min="0"
          step={field.integer ? "1" : "any"}
          inputMode="decimal"
          placeholder="0"
          value={value ?? ""}
          onChange={(event) => onChange(event.target.value)}
        />
        {error && <p className="error-text">{error}</p>}
      </div>
    );
  }

  return (
    <div className="field">
      <label>{field.label}</label>
      <textarea
        rows={2}
        placeholder={field.placeholder}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}
