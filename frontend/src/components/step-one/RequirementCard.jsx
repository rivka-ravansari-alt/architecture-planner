import RequirementField from "./RequirementField.jsx";

/**
 * A collapsible requirement card. The enable toggle reveals the conditional
 * fields; when disabled, only the question is shown.
 * @param {{
 *   card: object,
 *   value: object,
 *   errors: Record<string, string>,
 *   onToggle: (cardId: string) => void,
 *   onFieldChange: (cardId: string, fieldKey: string, value: any) => void,
 * }} props
 */
export default function RequirementCard({
  card,
  value,
  errors,
  onToggle,
  onFieldChange,
}) {
  const enabled = Boolean(value.enabled);
  const hasFields = card.fields.length > 0;
  const contentId = `req-${card.id}-content`;

  return (
    <div className={`req-card${enabled ? " req-card-active" : ""}`}>
      <div className="req-card-head">
        <div className="req-card-heading">
          <h3 className="req-card-title">{card.title}</h3>
          <p className="req-card-question">{card.question}</p>
        </div>
        <label className="switch" aria-label={card.title}>
          <input
            type="checkbox"
            checked={enabled}
            aria-expanded={hasFields ? enabled : undefined}
            aria-controls={hasFields ? contentId : undefined}
            onChange={() => onToggle(card.id)}
          />
          <span className="slider" />
        </label>
      </div>

      {hasFields && (
        <div
          id={contentId}
          className={`toggle-section-content${enabled ? " open" : ""}`}
        >
          <div className="toggle-section-inner">
            {card.fields.map((field) => (
              <RequirementField
                key={field.key}
                field={field}
                value={value[field.key]}
                error={errors[`${card.id}.${field.key}`]}
                onChange={(fieldValue) =>
                  onFieldChange(card.id, field.key, fieldValue)
                }
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
