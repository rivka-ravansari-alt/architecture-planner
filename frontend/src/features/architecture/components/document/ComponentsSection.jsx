import ComponentCard from "./ComponentCard.jsx";
import DocSubheading from "./DocSubheading.jsx";

function ComponentGroup({ title, items, emptyMessage, onMove }) {
  return (
    <>
      <DocSubheading>{title}</DocSubheading>
      {items.length === 0 ? (
        <p className="muted doc-empty">{emptyMessage}</p>
      ) : (
        <div className="doc-component-grid">
          {items.map((component) => (
            <ComponentCard key={component._i} component={component} onMove={onMove} />
          ))}
        </div>
      )}
    </>
  );
}

export default function ComponentsSection({ required, optional, onMove }) {
  return (
    <>
      <ComponentGroup
        title="Required Components"
        items={required}
        emptyMessage="No required components in the current plan."
        onMove={onMove}
      />
      <ComponentGroup
        title="Optional Components"
        items={optional}
        emptyMessage="No optional components selected."
        onMove={onMove}
      />
    </>
  );
}
