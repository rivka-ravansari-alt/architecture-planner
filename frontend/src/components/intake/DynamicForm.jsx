import { INTAKE_FORM_CONFIG } from "../../config/intakeFormConfig.js";
import { DESCRIPTION_MAX_CHARS } from "../../constants/wizard.js";
import {
  setFeatureEnabled,
  setFeatureField,
  setProductField,
  togglePlatform,
} from "../../utils/intakeFormState.js";
import FieldRenderer from "./FieldRenderer.jsx";
import ToggleSection from "./ToggleSection.jsx";

const { productSection, architectureSection } = INTAKE_FORM_CONFIG;

const SCALE_FIELD_KEYS = new Set(["stage", "expected_users"]);

/**
 * @param {Object} props
 * @param {"basic" | "features" | "all"} [props.section]
 * @param {ReturnType<import("../../utils/intakeFormState.js").createEmptyIntakeForm>} props.value
 * @param {(next: ReturnType<import("../../utils/intakeFormState.js").createEmptyIntakeForm>) => void} props.onChange
 * @param {Record<string, string>} [props.errors]
 */
export default function DynamicForm({ section = "all", value, onChange, errors = {} }) {
  const showBasic = section === "basic" || section === "all";
  const showFeatures = section === "features" || section === "all";

  const descriptionLength = String(value.product.description || "").length;
  const descriptionOverLimit = descriptionLength > DESCRIPTION_MAX_CHARS;

  const handleProductChange = (fieldKey, fieldValue) => {
    if (fieldKey === "stage" && fieldValue === "production") {
      return;
    }

    onChange(setProductField(value, fieldKey, fieldValue));
  };

  const handlePlatformToggle = (optionValue) => {
    onChange(togglePlatform(value, "platforms", optionValue));
  };

  const handleFeatureToggle = (featureKey, enabled) => {
    onChange(setFeatureEnabled(value, featureKey, enabled));
  };

  const handleFeatureFieldChange = (featureKey, fieldKey, fieldValue) => {
    onChange(setFeatureField(value, featureKey, fieldKey, fieldValue));
  };

  const renderProductField = (field) => (
    <div key={field.key}>
      <FieldRenderer
        field={field}
        value={value.product[field.key]}
        onChange={(fieldValue) => handleProductChange(field.key, fieldValue)}
        error={errors[field.key]}
        onPlatformToggle={field.key === "platforms" ? handlePlatformToggle : undefined}
      />
      {field.key === "description" && (
        <div className={`field-hint-sm ${descriptionOverLimit ? "error-text" : ""}`}>
          {descriptionLength} / {DESCRIPTION_MAX_CHARS}
        </div>
      )}
    </div>
  );

  const primaryFields = productSection.fields.filter((field) => !SCALE_FIELD_KEYS.has(field.key));
  const scaleFields = productSection.fields.filter((field) => SCALE_FIELD_KEYS.has(field.key));

  return (
    <div className="dynamic-form">
      {showBasic && (
        <div className="card">
          <h2>{productSection.title}</h2>
          <p className="subtitle">{productSection.subtitle}</p>

          {primaryFields.map(renderProductField)}

          <div className="grid-2">{scaleFields.map(renderProductField)}</div>
        </div>
      )}

      {showFeatures && (
        <div className="card intake-features-card">
          <h2>{architectureSection.title}</h2>
          <p className="subtitle">{architectureSection.subtitle}</p>

          {architectureSection.toggles.map((toggle) => (
            <ToggleSection
              key={toggle.key}
              toggle={toggle}
              featureState={value.features[toggle.key]}
              onToggle={(enabled) => handleFeatureToggle(toggle.key, enabled)}
              onFieldChange={(fieldKey, fieldValue) =>
                handleFeatureFieldChange(toggle.key, fieldKey, fieldValue)
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
