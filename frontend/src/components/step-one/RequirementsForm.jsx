import RequirementCard from "./RequirementCard.jsx";
import {
  REQUIREMENT_CARDS,
  buildInitialRequirements,
  serializeRequirements,
  validateRequirements,
} from "./requirementsConfig.js";

export {
  REQUIREMENT_CARDS,
  buildInitialRequirements,
  serializeRequirements,
  validateRequirements,
};

/**
 * Requirements form: business-level requirement cards producing structured JSON.
 * @param {{ value: object, onChange: (value: object) => void }} props
 */
export default function RequirementsForm({ value, onChange }) {
  const errors = validateRequirements(value);

  const toggleCard = (cardId) => {
    const current = value[cardId] ?? { enabled: false };
    onChange({ ...value, [cardId]: { ...current, enabled: !current.enabled } });
  };

  const setField = (cardId, fieldKey, fieldValue) => {
    const current = value[cardId] ?? { enabled: true };
    onChange({ ...value, [cardId]: { ...current, [fieldKey]: fieldValue } });
  };

  return (
    <div className="req-list">
      {REQUIREMENT_CARDS.map((card) => (
        <RequirementCard
          key={card.id}
          card={card}
          value={value[card.id] ?? { enabled: false }}
          errors={errors}
          onToggle={toggleCard}
          onFieldChange={setField}
        />
      ))}
    </div>
  );
}
