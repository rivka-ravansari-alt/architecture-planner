import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import ComponentCard from "../../features/architecture/components/document/ComponentCard.jsx";
import DocSubheading from "../../features/architecture/components/document/DocSubheading.jsx";
import { Spinner } from "../ui/Spinner.jsx";
import ComponentFormPanel from "./ComponentFormPanel.jsx";

export default function StepComponentReview({
  components,
  loading,
  onMove,
  onRemove,
  onAdd,
  onUpdate,
  onGenerateArchitecture,
}) {
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelMode, setPanelMode] = useState("create");
  const [editingIndex, setEditingIndex] = useState(null);

  const indexed = components.map((component, index) => ({ ...component, _i: index }));
  const required = indexed.filter((component) => !component.optional);
  const optional = indexed.filter((component) => component.optional);

  const existingKeys = useMemo(
    () => new Set(components.map((component) => component.key)),
    [components]
  );

  const editingComponent = editingIndex === null ? null : components[editingIndex] ?? null;

  const openCreatePanel = () => {
    setPanelMode("create");
    setEditingIndex(null);
    setPanelOpen(true);
  };

  const openEditPanel = (index) => {
    setPanelMode("edit");
    setEditingIndex(index);
    setPanelOpen(true);
  };

  const closePanel = () => {
    setPanelOpen(false);
    setEditingIndex(null);
  };

  const handleSubmit = (component) => {
    if (panelMode === "edit" && editingIndex !== null) {
      onUpdate(editingIndex, component);
      return;
    }
    onAdd(component);
  };

  return (
    <section className="panel">
      <header className="panel-head">
        <h2 className="panel-title">Component Review</h2>
        <p className="panel-sub">
          Approve the generated components, remove anything unnecessary, adjust required/optional
          status, or add your own. When ready, generate the architecture diagrams.
        </p>
      </header>

      <div className="component-review-body">
        <ComponentGroup
          title="Required Components"
          items={required}
          emptyMessage="No required components in the current plan."
          onMove={onMove}
          onRemove={onRemove}
          onEdit={openEditPanel}
        />
        <ComponentGroup
          title="Optional Components"
          items={optional}
          emptyMessage="No optional components selected."
          onMove={onMove}
          onRemove={onRemove}
          onEdit={openEditPanel}
        />

        <div className="component-review-toolbar">
          <button
            type="button"
            className="btn btn-ghost component-review-add"
            onClick={openCreatePanel}
            disabled={loading}
          >
            <Plus size={16} strokeWidth={2} aria-hidden="true" />
            Add Component
          </button>
        </div>
      </div>

      <div className="actions component-review-actions">
        <span />
        <button
          type="button"
          className="btn btn-primary"
          onClick={onGenerateArchitecture}
          disabled={loading || components.length === 0}
        >
          {loading && <Spinner />}
          {loading ? "Generating architecture… (may take a few seconds)" : "Generate Architecture"}
        </button>
      </div>

      <ComponentFormPanel
        open={panelOpen}
        mode={panelMode}
        initialComponent={editingComponent}
        existingKeys={existingKeys}
        onClose={closePanel}
        onSubmit={handleSubmit}
      />
    </section>
  );
}

function ComponentGroup({ title, items, emptyMessage, onMove, onRemove, onEdit }) {
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
              onMove={onMove}
              onRemove={onRemove}
              onEdit={() => onEdit(component._i)}
            />
          ))}
        </div>
      )}
    </>
  );
}
