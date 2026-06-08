import Badge from "../../../../components/ui/Badge.jsx";
import { getComponentIcon, normalizeComponentType } from "../../../../constants/componentTypes.js";
import { truncateToSentences } from "../../../../utils/text.js";
import ImplementationOptionsDetails from "./ImplementationOptionsDetails.jsx";

export default function ComponentCard({ component, onMove }) {
  const isOptional = component.optional;
  const Icon = getComponentIcon(normalizeComponentType(component.type));

  return (
    <article className="doc-component-card">
      <div className="doc-component-head">
        <div className="doc-component-title">
          <span className="doc-component-icon" aria-hidden="true">
            <Icon size={18} strokeWidth={1.75} />
          </span>
          <h4 className="doc-component-name">{component.name}</h4>
        </div>
        <Badge variant={isOptional ? "optional" : "required"}>
          {isOptional ? "Optional" : "Required"}
        </Badge>
      </div>
      <ImplementationOptionsDetails implementationOptions={component.implementation_options} />
      <p className="doc-component-reason">{truncateToSentences(component.reason)}</p>
      <div className="doc-component-actions">
        <button
          type="button"
          className="btn-move"
          onClick={() => onMove(component._i, !isOptional)}
        >
          {isOptional ? "Move to Required" : "Move to Optional"}
        </button>
      </div>
    </article>
  );
}
