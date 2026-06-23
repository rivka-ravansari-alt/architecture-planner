import { EXPECTED_USERS, STAGES } from "../../../../constants/wizard.js";
import { labelFor, truncateToSentences } from "../../../../utils/text.js";
import DocSubheading from "./DocSubheading.jsx";

const WORKFLOW_LABELS = {
  DRAFT: "Draft",
  COMPONENTS_GENERATED: "Components generated",
  COMPONENTS_APPROVED: "Components approved",
  DIAGRAMS_GENERATED: "Diagrams generated",
  ARCHITECTURE_APPROVED: "Architecture approved",
  PRICING_GENERATED: "Pricing generated",
};

export default function OverviewSection({ project, projectTypes, requiredCount, optionalCount }) {
  const typeLabels = project.project_types
    .map((type) => projectTypes.find((item) => item.id === type)?.label || type)
    .join(", ");

  return (
    <>
      <DocSubheading>Project Summary</DocSubheading>
      <div className="summary-grid doc-summary-grid">
        <div className="summary-item">
          <div className="k">Name</div>
          <div className="v">{project.name}</div>
        </div>
        <div className="summary-item">
          <div className="k">Type</div>
          <div className="v">{typeLabels}</div>
        </div>
        <div className="summary-item">
          <div className="k">Stage</div>
          <div className="v">{labelFor(STAGES, project.stage)}</div>
        </div>
        <div className="summary-item">
          <div className="k">Expected Users</div>
          <div className="v">{labelFor(EXPECTED_USERS, project.expected_users)}</div>
        </div>
      </div>

      <DocSubheading>Architecture Summary</DocSubheading>
      {project.architecture_summary ? (
        <p className="doc-text">{truncateToSentences(project.architecture_summary, 4)}</p>
      ) : (
        <p className="muted doc-empty">No architecture summary available.</p>
      )}

      <DocSubheading>Generation Status</DocSubheading>
      <div className="doc-status-grid">
        <div className="doc-status-item">
          <span className="doc-status-label">Workflow</span>
          <span className="doc-status-value">
            {WORKFLOW_LABELS[project.workflow_status] || project.workflow_status}
          </span>
        </div>
        <div className="doc-status-item">
          <span className="doc-status-label">Components</span>
          <span className="doc-status-value">
            {requiredCount} required · {optionalCount} optional
          </span>
        </div>
        <div className="doc-status-item">
          <span className="doc-status-label">Flow steps</span>
          <span className="doc-status-value">{project.main_flow?.length || 0}</span>
        </div>
      </div>
    </>
  );
}
