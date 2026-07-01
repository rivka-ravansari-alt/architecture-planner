import { INTAKE_FORM_CONFIG } from "../../config/intakeFormConfig.js";
import { DESCRIPTION_MAX_CHARS } from "../../constants/wizard.js";
import { setProductField, togglePlatform } from "../../utils/intakeFormState.js";
import FieldRenderer from "./FieldRenderer.jsx";

const { productSection } = INTAKE_FORM_CONFIG;

/**
 * @param {Object} props
 * @param {"basic" | "features" | "all"} [props.section]
 * @param {ReturnType<import("../../utils/intakeFormState.js").createEmptyIntakeForm>} props.value
 * @param {(next: ReturnType<import("../../utils/intakeFormState.js").createEmptyIntakeForm>) => void} props.onChange
 * @param {Record<string, string>} [props.errors]
 * @param {boolean} [props.showHeader]
 */
export default function DynamicForm({
  section = "all",
  value,
  onChange,
  errors = {},
  showHeader = true,
}) {
  const showBasic = section === "basic" || section === "all";

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

  return (
    <div className="dynamic-form">
      {showBasic && (
        <div className="card">
          {showHeader && (
            <>
              <h2>{productSection.title}</h2>
              <p className="subtitle">{productSection.subtitle}</p>
            </>
          )}

          {productSection.fields.map(renderProductField)}
        </div>
      )}
    </div>
  );
}
