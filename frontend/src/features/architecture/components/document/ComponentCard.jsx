import Badge from "../../../../components/ui/Badge.jsx";
import DropdownMenu from "../../../../components/ui/DropdownMenu.jsx";
import {
  formatComponentTypeLabel,
  getComponentIcon,
  getComponentSourceLabel,
  isUserAddedComponent,
  normalizeComponentType,
} from "../../../../constants/componentTypes.js";
import { truncateToSentences } from "../../../../utils/text.js";
import ImplementationOptionsDetails from "./ImplementationOptionsDetails.jsx";

export default function ComponentCard({ component, onMove, onRemove, onEdit }) {
  const isOptional = component.optional;
  const Icon = getComponentIcon(normalizeComponentType(component.type));
  const typeLabel = formatComponentTypeLabel(component.type);
  const sourceLabel = getComponentSourceLabel(component.source);
  const sourceVariant = isUserAddedComponent(component) ? "user-added" : "ai-generated";
  const showUserEdit = onEdit && isUserAddedComponent(component);

  const menuItems = [];
  if (showUserEdit) {
    menuItems.push({ label: "Edit", onClick: onEdit });
  }
  if (onMove) {
    menuItems.push({
      label: isOptional ? "Move to Required" : "Move to Optional",
      onClick: () => onMove(component._i, !isOptional),
    });
  }
  if (onRemove) {
    menuItems.push({
      label: "Remove",
      onClick: () => onRemove(component._i),
      destructive: true,
    });
  }

  const hasMenu = menuItems.length > 0;

  return (
    <article className="doc-component-card">
      <div className="doc-component-head">
        <div className="doc-component-title">
          <span className="doc-component-icon" aria-hidden="true">
            <Icon size={18} strokeWidth={1.75} />
          </span>
          <div className="doc-component-title-text">
            <h4 className="doc-component-name">{component.name}</h4>
            <p className="doc-component-type">{typeLabel}</p>
          </div>
        </div>
        {hasMenu && <DropdownMenu label={`Actions for ${component.name}`} items={menuItems} />}
      </div>

      <div className="doc-component-badges">
        <Badge variant={sourceVariant}>{sourceLabel}</Badge>
      </div>

      <ImplementationOptionsDetails implementationOptions={component.implementation_options} />
      <p className="doc-component-reason">{truncateToSentences(component.reason)}</p>
    </article>
  );
}
