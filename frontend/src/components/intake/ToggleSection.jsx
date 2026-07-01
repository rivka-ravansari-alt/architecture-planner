import FieldRenderer from "./FieldRenderer.jsx";
import QuestionTitle from "./QuestionTitle.jsx";

/**
 * @param {Object} props
 * @param {import("../../config/intakeFormConfig.js").UsageToggleGroup} props.toggle
 * @param {Record<string, unknown>} props.featureState
 * @param {(enabled: boolean) => void} props.onToggle
 * @param {(fieldKey: string, value: unknown) => void} props.onFieldChange
 * @param {(field: import("../../config/intakeFormConfig.js").FormField) => boolean} [props.isFieldVisible]
 */
export default function ToggleSection({
  toggle,
  featureState,
  onToggle,
  onFieldChange,
  isFieldVisible = () => true,
}) {
  const enabled = Boolean(featureState.enabled);
  const visibleFields = toggle.fields.filter(isFieldVisible);
  const hasSubQuestions = visibleFields.length > 0;

  return (
    <section className={`usage-question-block toggle-section ${enabled ? "toggle-section-active" : ""}`}>
      <QuestionTitle
        title={toggle.title}
        description={toggle.description}
        examples={toggle.examples}
      />
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
            {visibleFields.map((field) => (
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
    </section>
  );
}
