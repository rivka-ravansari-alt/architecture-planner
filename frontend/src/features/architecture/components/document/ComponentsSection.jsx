import ComponentGroup from "./ComponentGroup.jsx";

export default function ComponentsSection({ required, optional, onMove, readOnly = false }) {
  return (
    <>
      <ComponentGroup
        title="Required Components"
        items={required}
        emptyMessage="No required components in the current plan."
        onMove={onMove}
        readOnly={readOnly}
      />
      <ComponentGroup
        title="Optional Components"
        items={optional}
        emptyMessage="No optional components selected."
        onMove={onMove}
        readOnly={readOnly}
      />
    </>
  );
}
