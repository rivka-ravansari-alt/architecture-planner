import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import ComponentGroup from "../../features/architecture/components/document/ComponentGroup.jsx";
import { Spinner } from "../ui/Spinner.jsx";
import { partitionIndexedComponents } from "../../utils/components.js";
import ComponentFormPanel from "./ComponentFormPanel.jsx";

export default function StepComponentReview({
  components,
  componentCatalog = [],
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

  const { required, optional } = partitionIndexedComponents(components);

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
        componentCatalog={componentCatalog}
        onClose={closePanel}
        onSubmit={handleSubmit}
      />
    </section>
  );
}
