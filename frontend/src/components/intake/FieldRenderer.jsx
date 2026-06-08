import { isPlatformSelected } from "../../utils/intakeFormState.js";

/**
 * @param {Object} props
 * @param {import("../../config/intakeFormConfig.js").FormField} props.field
 * @param {unknown} props.value
 * @param {(value: unknown) => void} props.onChange
 * @param {string} [props.error]
 * @param {(optionValue: string) => void} [props.onPlatformToggle]
 */
export default function FieldRenderer({
  field,
  value,
  onChange,
  error,
  onPlatformToggle,
}) {
  const fieldId = `field-${field.key}`;

  if (field.type === "text") {
    return (
      <div className="field">
        <label htmlFor={fieldId}>{field.label}</label>
        <input
          id={fieldId}
          type="text"
          placeholder={field.placeholder}
          value={typeof value === "string" ? value : ""}
          onChange={(event) => onChange(event.target.value)}
        />
        {error && <div className="error-text">{error}</div>}
      </div>
    );
  }

  if (field.type === "textarea") {
    return (
      <div className="field">
        <label htmlFor={fieldId}>{field.label}</label>
        <textarea
          id={fieldId}
          placeholder={field.placeholder}
          value={typeof value === "string" ? value : ""}
          onChange={(event) => onChange(event.target.value)}
        />
        {error && <div className="error-text">{error}</div>}
      </div>
    );
  }

  if (field.type === "select") {
    return (
      <div className="field">
        <label htmlFor={fieldId}>{field.label}</label>
        <select
          id={fieldId}
          value={typeof value === "string" ? value : ""}
          onChange={(event) => onChange(event.target.value)}
        >
          {!field.required && <option value="">Select...</option>}
          {field.options?.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {error && <div className="error-text">{error}</div>}
      </div>
    );
  }

  if (field.type === "multi_select") {
    const selectedValues = Array.isArray(value) ? value : [];
    const isPlatformField = field.key === "platforms";

    return (
      <div className="field">
        <label>{field.label}</label>
        <div className="chips">
          {field.options?.map((option) => {
            const selected = isPlatformField
              ? isPlatformSelected(selectedValues, option.value)
              : selectedValues.includes(option.value);

            const handleClick = () => {
              if (isPlatformField && onPlatformToggle) {
                onPlatformToggle(option.value);
                return;
              }

              const exists = selectedValues.includes(option.value);
              onChange(
                exists
                  ? selectedValues.filter((item) => item !== option.value)
                  : [...selectedValues, option.value]
              );
            };

            return (
              <div
                key={option.value}
                className={`chip ${selected ? "selected" : ""}`}
                onClick={handleClick}
                role="button"
                tabIndex={0}
                onKeyDown={(event) =>
                  (event.key === "Enter" || event.key === " ") && handleClick()
                }
              >
                {option.label}
              </div>
            );
          })}
        </div>
        {error && <div className="error-text">{error}</div>}
      </div>
    );
  }

  if (field.type === "checkbox_group") {
    const selectedValues = Array.isArray(value) ? value : [];

    return (
      <div className="field">
        <label>{field.label}</label>
        <div className="option-group">
          {field.options?.map((option) => {
            const checked = selectedValues.includes(option.value);
            return (
              <label key={option.value} className="option-check">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() =>
                    onChange(
                      checked
                        ? selectedValues.filter((item) => item !== option.value)
                        : [...selectedValues, option.value]
                    )
                  }
                />
                <span>{option.label}</span>
              </label>
            );
          })}
        </div>
      </div>
    );
  }

  if (field.type === "radio") {
    return (
      <div className="field">
        <label>{field.label}</label>
        <div className="option-group">
          {field.options?.map((option) => (
            <label key={option.value} className="option-check">
              <input
                type="radio"
                name={fieldId}
                checked={value === option.value}
                onChange={() => onChange(option.value)}
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
        {error && <div className="error-text">{error}</div>}
      </div>
    );
  }

  if (field.type === "boolean") {
    return (
      <div className="toggle-row toggle-row-nested">
        <span className="label">{field.label}</span>
        <label className="switch">
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(event) => onChange(event.target.checked)}
          />
          <span className="slider" />
        </label>
      </div>
    );
  }

  return null;
}
