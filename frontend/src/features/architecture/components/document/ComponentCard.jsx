import DropdownMenu from "../../../../components/ui/DropdownMenu.jsx";
import {
  formatComponentTypeLabel,
  getComponentIcon,
  isUserAddedComponent,
  normalizeComponentType,
} from "../../../../constants/componentTypes.js";
import {
  normalizeCloudMappings,
  selectedCloudService,
} from "../../../../utils/cloudMappings.js";
import { truncateToSentences } from "../../../../utils/text.js";

const CLOUD_PROVIDERS = [
  { id: "aws", label: "AWS" },
  { id: "gcp", label: "Google Cloud" },
  { id: "azure", label: "Azure" },
];

export default function ComponentCard({ component, onMove, onRemove, onEdit }) {
  const isOptional = component.optional;
  const Icon = getComponentIcon(normalizeComponentType(component.type));
  const typeLabel = formatComponentTypeLabel(component.type);
  const showUserEdit = onEdit && isUserAddedComponent(component);
  const cloudMappings = normalizeCloudMappings(component);

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

      <p className="doc-component-reason">
        <strong>Description:</strong> {truncateToSentences(component.reason)}
      </p>

      <div className="doc-component-cloud-mappings" aria-label="Selected pricing services">
        <span className="doc-component-cloud-label">Selected Pricing Services</span>
        <div className="doc-component-cloud-cards">
          {CLOUD_PROVIDERS.map(({ id, label }) => {
            const service = selectedCloudService(cloudMappings[id]);

            return (
              <div
                key={id}
                className={`doc-cloud-service-card provider-${id}${service ? "" : " is-not-mapped"}`}
                aria-label={`${label}: ${service || "Not mapped"}`}
              >
                <div className="doc-cloud-provider-meta">
                  <span className={`doc-cloud-provider-logo provider-${id}`} aria-hidden="true">
                    <span className="doc-cloud-provider-mark" />
                  </span>
                  <span className="doc-cloud-provider-name">{label}</span>
                </div>
                <p className="doc-cloud-service-name">{service || "Not mapped"}</p>
              </div>
            );
          })}
        </div>
      </div>
    </article>
  );
}
