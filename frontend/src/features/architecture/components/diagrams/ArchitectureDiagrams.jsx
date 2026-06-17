import { useState } from "react";
import ArchitectureDiagram from "./ArchitectureDiagram.jsx";
import MermaidDiagram from "./MermaidDiagram.jsx";
import { resolveArchitectureDiagrams } from "./diagramHelpers.js";

export default function ArchitectureDiagrams({ project, components }) {
  const entries = resolveArchitectureDiagrams(project);
  const [activeKey, setActiveKey] = useState(() => entries[0]?.key ?? "high_level");

  if (!entries.length) {
    return <p className="muted doc-empty">No architecture diagrams available.</p>;
  }

  const activeEntry = entries.find((e) => e.key === activeKey) ?? entries[0];

  return (
    <div className="arch-diagram-workspace">
      <div className="arch-diagram-tabs" role="tablist" aria-label="Architecture diagram views">
        {entries.map((entry) => {
          const isActive = entry.key === activeEntry.key;
          return (
            <button
              key={entry.key}
              type="button"
              role="tab"
              id={`diagram-tab-${entry.key}`}
              aria-selected={isActive}
              aria-controls="diagram-workspace-panel"
              className={`arch-diagram-tab${isActive ? " is-active" : ""}`}
              onClick={() => setActiveKey(entry.key)}
            >
              {entry.tabLabel}
            </button>
          );
        })}
      </div>

      <div
        className="arch-diagram-workspace-panel"
        id="diagram-workspace-panel"
        role="tabpanel"
        aria-labelledby={`diagram-tab-${activeEntry.key}`}
      >
        {activeEntry.description && (
          <p className="arch-diagram-workspace-desc">{activeEntry.description}</p>
        )}
        <div className="arch-diagram-workspace-canvas">
          {activeEntry.diagram.type === "mermaid" ? (
            <MermaidDiagram key={activeEntry.key} diagram={activeEntry.diagram} />
          ) : (
            <ArchitectureDiagram
              key={activeEntry.key}
              diagram={activeEntry.diagram}
              diagramType={activeEntry.key}
              components={components}
            />
          )}
        </div>
      </div>
    </div>
  );
}
