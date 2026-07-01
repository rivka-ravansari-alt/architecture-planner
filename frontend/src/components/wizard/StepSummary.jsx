import {
  AI_REQUESTS_PER_USER_OPTIONS,
  BACKGROUND_JOBS_OPTIONS,
  FILE_SIZE_OPTIONS,
  MONTHLY_ACTIVE_USERS_OPTIONS,
  NOTIFICATION_CHANNEL_OPTIONS,
  NOTIFICATION_VOLUME_OPTIONS,
  USER_ACTIVITY_OPTIONS,
  USAGE_TOGGLE_GROUPS,
} from "../../config/intakeFormConfig.js";
import { STAGES } from "../../constants/wizard.js";
import { resolveExpectedUsers } from "../../utils/intakeFormMapper.js";
import ComponentGroup from "../../features/architecture/components/document/ComponentGroup.jsx";
import ArchitectureDiagrams from "../../features/architecture/components/diagrams/ArchitectureDiagrams.jsx";
import CloudCostsSection from "../../features/architecture/components/document/CloudCostsSection.jsx";
import { FlowList } from "../../features/architecture/components/document/DocumentLists.jsx";
import { labelFor } from "../../utils/text.js";
import { partitionIndexedComponents } from "../../utils/components.js";

function labelFromOptions(options, value) {
  return options.find((item) => item.value === value)?.label || value || "—";
}

function RequirementsSummary({ intakeForm }) {
  const usage = intakeForm.usage;
  const enabledToggles = USAGE_TOGGLE_GROUPS.filter((toggle) => usage[toggle.key]?.enabled);
  const notificationChannels =
    usage.notifications?.enabled && Array.isArray(usage.notifications?.channels)
      ? usage.notifications.channels
      : [];

  return (
    <ul className="summary-requirements-list">
      <li>
        Monthly active users:{" "}
        {usage.monthly_active_users === "custom"
          ? Number(usage.custom_monthly_active_users || 0).toLocaleString()
          : labelFromOptions(MONTHLY_ACTIVE_USERS_OPTIONS, usage.monthly_active_users)}
      </li>
      <li>User activity: {labelFromOptions(USER_ACTIVITY_OPTIONS, usage.user_activity)}</li>
      <li>
        Background tasks: {labelFromOptions(BACKGROUND_JOBS_OPTIONS, usage.background_jobs)}
      </li>
      {enabledToggles.map((toggle) => (
        <li key={toggle.key}>{toggle.title}: Yes</li>
      ))}
      {notificationChannels.length > 0 && (
        <li>
          Notifications:{" "}
          {notificationChannels
            .map((channel) =>
              labelFromOptions(NOTIFICATION_CHANNEL_OPTIONS, channel)
            )
            .join(", ")}{" "}
          ({labelFromOptions(
            NOTIFICATION_VOLUME_OPTIONS,
            usage.notifications?.volume_per_month
          )}{" "}
          / month)
        </li>
      )}
      {usage.file_uploads?.enabled && (
        <li>
          File uploads: {labelFromOptions(FILE_SIZE_OPTIONS, usage.file_uploads.average_file_size)}{" "}
          avg size
        </li>
      )}
      {usage.ai?.enabled && (
        <li>
          AI usage:{" "}
          {labelFromOptions(
            AI_REQUESTS_PER_USER_OPTIONS,
            usage.ai.requests_per_user_per_day
          )}{" "}
          requests / user / day
        </li>
      )}
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
          {resolveExpectedUsers(intakeForm.usage || {}) || project?.expected_users || "—"}
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
          <h3 className="wizard-section-title">Usage Profile</h3>
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

        {(costs?.length ?? 0) > 0 && (
          <section className="summary-step-section">
            <h3 className="wizard-section-title">Pricing</h3>
            <CloudCostsSection components={components} costs={costs} />
          </section>
        )}
      </div>
    </section>
  );
}
