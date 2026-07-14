/**
 * A single architecture component card.
 * Shows the category name, description, and the selection reason.
 * The raw category id is preserved in a data attribute for later mapping/pricing.
 * The instance id is preserved for edit/remove operations.
 *
 * When `onRemove` is provided a remove action is rendered; the card is otherwise
 * identical for AI-selected and user-added components.
 *
 * @param {{
 *   component: import("../../api/projectApi.js").SelectedComponent,
 *   variant?: "selected"|"excluded",
 *   onRemove?: (component: import("../../api/projectApi.js").SelectedComponent) => void,
 *   removing?: boolean,
 * }} props
 */
export default function ComponentReviewCard({
  component,
  variant = "selected",
  onRemove,
  removing = false,
}) {
  return (
    <article
      className={`component-review-card ${variant}`}
      data-instance-id={component.instance_id}
      data-category-id={component.category_id}
    >
      <div className="component-review-head">
        <h3 className="component-review-name">{component.name}</h3>
        <div className="component-review-head-meta">
          {component.type && (
            <span className="component-review-type">{component.type}</span>
          )}
          {onRemove && (
            <button
              type="button"
              className="component-review-remove"
              aria-label={`Remove ${component.name}`}
              title="Remove component"
              disabled={removing}
              onClick={() => onRemove(component)}
            >
              ×
            </button>
          )}
        </div>
      </div>
      {component.description && (
        <p className="component-review-description">{component.description}</p>
      )}
      <p className="component-review-reason">{component.reason}</p>
    </article>
  );
}
