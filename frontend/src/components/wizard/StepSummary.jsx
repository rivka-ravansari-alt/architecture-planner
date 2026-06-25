import { FEATURE_TOGGLES } from "../../config/intakeFormConfig.js";
import { EXPECTED_USERS, STAGES } from "../../constants/wizard.js";
import ComponentGroup from "../../features/architecture/components/document/ComponentGroup.jsx";
import ArchitectureDiagrams from "../../features/architecture/components/diagrams/ArchitectureDiagrams.jsx";
import CloudCostsSection from "../../features/architecture/components/document/CloudCostsSection.jsx";
import { FlowList } from "../../features/architecture/components/document/DocumentLists.jsx";
import { labelFor } from "../../utils/text.js";
import { partitionIndexedComponents } from "../../utils/components.js";

function RequirementsSummary({ intakeForm }) {
  const enabled = FEATURE_TOGGLES.filter((toggle) => intakeForm.features[toggle.key]?.enabled);

  if (enabled.length === 0) {
    return <p className="muted doc-empty">No architecture capabilities were selected.</p>;
  }

  return (
    <ul className="summary-requirements-list">
      {enabled.map((toggle) => (
        <li key={toggle.key}>{toggle.label}</li>
      ))}
    </ul>
  );
}

function ProductSummary({ intakeForm, projectTypes, project }) {
  const product = intakeForm.product;
  const typeLabels = (project?.project_types || [])
    .map((type) => projectTypes.find((item) => item.id === type)?.label || type)
    .join(", ");

  return (
    <div className="summary-grid doc-summary-grid">
      <div className="summary-item">
        <div className="k">Name</div>
        <div className="v">{product.name || project?.name || "—"}</div>
      </div>
      <div className="summary-item">
        <div className="k">Platform</div>
        <div className="v">{typeLabels || "—"}</div>
      </div>
      <div className="summary-item">
        <div className="k">Stage</div>
        <div className="v">{labelFor(STAGES, product.stage || project?.stage)}</div>
      </div>
      <div className="summary-item">
        <div className="k">Expected users</div>
        <div className="v">
          {labelFor(EXPECTED_USERS, product.expected_users || project?.expected_users)}
        </div>
      </div>
      <div className="summary-item summary-item-wide">
        <div className="k">Description</div>
        <div className="v">{product.description || project?.description || "—"}</div>
      </div>
    </div>
  );
}

export default function StepSummary({
  intakeForm,
  project,
  projectTypes,
  components,
  costs,
  hasPricing,
}) {
  const { required, optional } = partitionIndexedComponents(components);

  return (
    <section className="panel panel-wide summary-step">
      <div className="summary-step-body">
        <section className="summary-step-section">
          <h3 className="wizard-section-title">Product</h3>
          <ProductSummary intakeForm={intakeForm} projectTypes={projectTypes} project={project} />
        </section>

        <section className="summary-step-section">
          <h3 className="wizard-section-title">Requirements</h3>
          <RequirementsSummary intakeForm={intakeForm} />
        </section>

        <section className="summary-step-section">
          <h3 className="wizard-section-title">Components</h3>
          <ComponentGroup
            title="Required Components"
            items={required}
            emptyMessage="No required components."
            readOnly
          />
          <ComponentGroup
            title="Optional Components"
            items={optional}
            emptyMessage="No optional components."
            readOnly
          />
        </section>

        <section className="summary-step-section">
          <h3 className="wizard-section-title">Architecture Diagrams</h3>
          <ArchitectureDiagrams project={project} components={components} />
        </section>

        <section className="summary-step-section">
          <h3 className="wizard-section-title">Architecture Flow</h3>
          <FlowList
            steps={project?.main_flow}
            emptyMessage="No architecture flow steps available."
          />
        </section>

        {hasPricing && (
          <section className="summary-step-section">
            <h3 className="wizard-section-title">Pricing</h3>
            <CloudCostsSection components={components} costs={costs} />
          </section>
        )}
      </div>
    </section>
  );
}
