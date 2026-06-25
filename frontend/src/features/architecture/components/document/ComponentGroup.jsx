import ComponentCard from "./ComponentCard.jsx";
import DocSubheading from "./DocSubheading.jsx";

export default function ComponentGroup({
  title,
  items,
  emptyMessage,
  onMove,
  onRemove,
  onEdit,
  readOnly = false,
}) {
  return (
    <>
      <DocSubheading>{title}</DocSubheading>
      {items.length === 0 ? (
        <p className="muted doc-empty">{emptyMessage}</p>
      ) : (
        <div className="doc-component-grid">
          {items.map((component) => (
            <ComponentCard
              key={component._i}
              component={component}
              onMove={readOnly ? null : onMove}
              onRemove={readOnly ? null : onRemove}
              onEdit={readOnly || !onEdit ? null : () => onEdit(component._i)}
            />
          ))}
        </div>
      )}
    </>
  );
}
