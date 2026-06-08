import FieldRenderer from "./FieldRenderer.jsx";

/**
 * @param {Object} props
 * @param {import("../../config/intakeFormConfig.js").FeatureToggle} props.toggle
 * @param {Record<string, unknown>} props.featureState
 * @param {(enabled: boolean) => void} props.onToggle
 * @param {(fieldKey: string, value: unknown) => void} props.onFieldChange
 */
export default function ToggleSection({
  toggle,
  featureState,
  onToggle,
  onFieldChange,
}) {
  const enabled = Boolean(featureState.enabled);
  const hasSubQuestions = toggle.fields.length > 0;

  return (
    <div className={`toggle-section ${enabled ? "toggle-section-active" : ""}`}>
      <div className="toggle-row">
        <span className="label">{toggle.label}</span>
        <label className="switch">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(event) => onToggle(event.target.checked)}
          />
          <span className="slider" />
        </label>
      </div>

      {hasSubQuestions && (
        <div className={`toggle-section-content ${enabled ? "open" : ""}`}>
          <div className="toggle-section-inner">
            {toggle.fields.map((field) => (
              <FieldRenderer
                key={field.key}
                field={field}
                value={featureState[field.key]}
                onChange={(value) => onFieldChange(field.key, value)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
