import { INTAKE_FORM_CONFIG } from "../../config/intakeFormConfig.js";
import {
  setUsageField,
  setUsageToggleEnabled,
  setUsageToggleField,
} from "../../utils/intakeFormState.js";
import FieldRenderer from "./FieldRenderer.jsx";
import QuestionTitle from "./QuestionTitle.jsx";
import ToggleSection from "./ToggleSection.jsx";

const { usageSection } = INTAKE_FORM_CONFIG;

/**
 * @param {import("../../config/intakeFormConfig.js").FormField} field
 * @param {Record<string, unknown>} usage
 */
function isFieldVisible(field, usage) {
  if (!field.showWhen) return true;
  return usage[field.showWhen.field] === field.showWhen.value;
}

/**
 * @param {import("../../config/intakeFormConfig.js").FormField} field
 * @param {Record<string, unknown>} featureState
 */
function isToggleFieldVisible(field, featureState) {
  if (field.requiresChannels) {
    const channels = Array.isArray(featureState.channels) ? featureState.channels : [];
    return channels.length > 0;
  }
  return true;
}

/**
 * @param {Object} props
 * @param {ReturnType<import("../../utils/intakeFormState.js").createEmptyIntakeForm>} props.value
 * @param {(next: ReturnType<import("../../utils/intakeFormState.js").createEmptyIntakeForm>) => void} props.onChange
 * @param {Record<string, string>} [props.errors]
 * @param {boolean} [props.showHeader]
 */
export default function UsageForm({ value, onChange, errors = {}, showHeader = true }) {
  const usage = value.usage;

  const handleUsageFieldChange = (fieldKey, fieldValue) => {
    onChange(setUsageField(value, fieldKey, fieldValue));
  };

  const handleToggle = (toggleKey, enabled) => {
    onChange(setUsageToggleEnabled(value, toggleKey, enabled));
  };

  const handleToggleFieldChange = (toggleKey, fieldKey, fieldValue) => {
    onChange(setUsageToggleField(value, toggleKey, fieldKey, fieldValue));
  };

  return (
    <div className="dynamic-form">
      <div className="card intake-features-card">
        {showHeader && (
          <>
            <h2>{usageSection.title}</h2>
            <p className="subtitle">{usageSection.subtitle}</p>
          </>
        )}

        {usageSection.questionBlocks.map((block) => (
          <section key={block.key} className="usage-question-block">
            <QuestionTitle
              title={block.title}
              description={block.description}
              examples={block.examples}
            />
            {block.fields
              .filter((field) => isFieldVisible(field, usage))
              .map((field) => (
                <FieldRenderer
                  key={field.key}
                  field={field}
                  value={usage[field.key]}
                  onChange={(fieldValue) => handleUsageFieldChange(field.key, fieldValue)}
                  error={errors[field.key]}
                />
              ))}
          </section>
        ))}

        {usageSection.toggleGroups.map((toggle) => (
          <ToggleSection
            key={toggle.key}
            toggle={toggle}
            featureState={usage[toggle.key]}
            onToggle={(enabled) => handleToggle(toggle.key, enabled)}
            onFieldChange={(fieldKey, fieldValue) =>
              handleToggleFieldChange(toggle.key, fieldKey, fieldValue)
            }
            isFieldVisible={(field) => isToggleFieldVisible(field, usage[toggle.key])}
          />
        ))}
      </div>
    </div>
  );
}
