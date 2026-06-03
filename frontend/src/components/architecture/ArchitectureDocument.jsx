import { EXPECTED_USERS, PROVIDER_LABELS, STAGES } from "../../constants.js";
import {
  formatCloudServices,
  groupRisksBySeverity,
  truncateToSentences,
} from "../../architectureHelpers.js";
import ArchitectureDiagrams from "./ArchitectureDiagrams.jsx";
import { getComponentIcon, normalizeComponentType } from "../../constants/componentTypes.js";

function labelFor(list, id) {
  return list.find((x) => x.id === id)?.label || id;
}

function DocSection({ id, title, expanded, onToggle, sectionRef, children }) {
  return (
    <section
      className="arch-doc-section"
      id={id}
      ref={(node) => sectionRef?.(id, node)}
    >
      <button
        type="button"
        className="arch-doc-section-toggle"
        onClick={onToggle}
        aria-expanded={expanded}
        aria-controls={`${id}-panel`}
      >
        <span className="arch-doc-chevron" aria-hidden="true">
          {expanded ? "▼" : "▶"}
        </span>
        <h2 className="arch-doc-section-title">{title}</h2>
      </button>
      {expanded && (
        <div className="arch-doc-section-body" id={`${id}-panel`}>
          {children}
        </div>
      )}
    </section>
  );
}

function DocSubheading({ children }) {
  return <h3 className="arch-doc-subheading">{children}</h3>;
}

function ComponentCard({ component, onMove }) {
  const isOptional = component.optional;
  const Icon = getComponentIcon(normalizeComponentType(component.type));
  return (
    <article className="doc-component-card">
      <div className="doc-component-head">
        <div className="doc-component-title">
          <span className="doc-component-icon" aria-hidden="true">
            <Icon size={18} strokeWidth={1.75} />
          </span>
          <h4 className="doc-component-name">{component.name}</h4>
        </div>
        <span className={`badge ${isOptional ? "optional" : "required"}`}>
          {isOptional ? "Optional" : "Required"}
        </span>
      </div>
      <p className="doc-component-reason">{truncateToSentences(component.reason)}</p>
      <div className="doc-component-actions">
        <button type="button" className="btn-move" onClick={() => onMove(component._i, !isOptional)}>
          {isOptional ? "Move to Required" : "Move to Optional"}
        </button>
      </div>
    </article>
  );
}

function RiskCard({ risk }) {
  return (
    <article className="doc-risk-card">
      <div className="doc-risk-head">
        <h4 className="doc-risk-title">{risk.title}</h4>
        <span className={`sev ${risk.severity}`}>{risk.severity}</span>
      </div>
      <p className="doc-risk-desc">{truncateToSentences(risk.description)}</p>
    </article>
  );
}

function FlowList({ steps, emptyMessage }) {
  if (!steps?.length) {
    return emptyMessage ? <p className="muted doc-empty">{emptyMessage}</p> : null;
  }
  return (
    <ol className="flow-list">
      {steps.map((step, i) => (
        <li key={i}>{step}</li>
      ))}
    </ol>
  );
}

function BulletList({ items, emptyMessage }) {
  if (!items?.length) {
    return emptyMessage ? <p className="muted doc-empty">{emptyMessage}</p> : null;
  }
  return (
    <ul className="doc-bullet-list">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

function ChecklistList({ items, emptyMessage }) {
  if (!items?.length) {
    return emptyMessage ? <p className="muted doc-empty">{emptyMessage}</p> : null;
  }
  return (
    <ul className="checklist-list">
      {items.map((item, i) => (
        <li key={i} className="checklist-item">
          <span className="checklist-marker" aria-hidden="true" />
          <span className="checklist-text">{item}</span>
        </li>
      ))}
    </ul>
  );
}

export default function ArchitectureDocument({
  project,
  projectTypes,
  components,
  onMove,
  risks,
  recommendations,
  costs,
  expandedSections,
  onToggleSection,
  sectionRef,
  showHero = true,
}) {
  const indexed = components.map((c, i) => ({ ...c, _i: i }));
  const required = indexed.filter((c) => !c.optional);
  const optional = indexed.filter((c) => c.optional);
  const typeLabels = project.project_types
    .map((t) => projectTypes.find((p) => p.id === t)?.label || t)
    .join(", ");
  const riskGroups = groupRisksBySeverity(risks);
  const componentsWithCloud = components.filter((c) => c.cloud_mapping);
  const hasOptionalCost = costs.some((c) => c.optionalHigh > 0);

  const sectionProps = (id) => ({
    id,
    sectionRef,
    expanded: expandedSections[id] !== false,
    onToggle: () => onToggleSection(id),
  });

  return (
    <article className="arch-doc-content">
      <DocSection title="Overview" {...sectionProps("overview")}>
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
            <span className="doc-status-label">Status</span>
            <span className={`doc-status-value ${project.generated_at ? "is-ok" : ""}`}>
              {project.generated_at ? "Generated" : "Pending"}
            </span>
          </div>
          <div className="doc-status-item">
            <span className="doc-status-label">Components</span>
            <span className="doc-status-value">
              {required.length} required · {optional.length} optional
            </span>
          </div>
          <div className="doc-status-item">
            <span className="doc-status-label">Flow steps</span>
            <span className="doc-status-value">{project.main_flow?.length || 0}</span>
          </div>
        </div>
      </DocSection>

      <DocSection title="Components" {...sectionProps("components")}>
        <DocSubheading>Required Components</DocSubheading>
        {required.length === 0 ? (
          <p className="muted doc-empty">No required components in the current plan.</p>
        ) : (
          <div className="doc-component-grid">
            {required.map((c) => (
              <ComponentCard key={c._i} component={c} onMove={onMove} />
            ))}
          </div>
        )}

        <DocSubheading>Optional Components</DocSubheading>
        {optional.length === 0 ? (
          <p className="muted doc-empty">No optional components selected.</p>
        ) : (
          <div className="doc-component-grid">
            {optional.map((c) => (
              <ComponentCard key={c._i} component={c} onMove={onMove} />
            ))}
          </div>
        )}
      </DocSection>

      <DocSection title="Architecture Diagrams" {...sectionProps("diagrams")}>
        <p className="doc-text doc-diagram-intro">
          Switch between three views — business overview, request flow, and technical
          implementation — using the tabs in the diagram workspace below.
        </p>
        <ArchitectureDiagrams project={project} components={components} />
      </DocSection>

      <DocSection title="Architecture Flow" {...sectionProps("flow")}>
        <FlowList steps={project.main_flow} emptyMessage="No architecture flow steps available." />
      </DocSection>

      <DocSection title="Risks" {...sectionProps("risks")}>
        {(["high", "medium", "low"]).map((level) => {
          const items = riskGroups[level];
          if (items.length === 0) return null;
          return (
            <div key={level} className="doc-risk-group">
              <DocSubheading>
                {level.charAt(0).toUpperCase() + level.slice(1)} Severity
              </DocSubheading>
              <div className="doc-risk-grid">
                {items.map((risk, i) => (
                  <RiskCard key={`${level}-${i}`} risk={risk} />
                ))}
              </div>
            </div>
          );
        })}
        {risks.length === 0 && (
          <p className="muted doc-empty">No notable risks identified.</p>
        )}
      </DocSection>

      <DocSection title="Recommendations" {...sectionProps("recommendations")}>
        <BulletList items={recommendations} emptyMessage="No recommendations at this time." />
      </DocSection>

      <DocSection title="Next Steps" {...sectionProps("next-steps")}>
        <ChecklistList
          items={project.next_steps}
          emptyMessage="No next steps defined."
        />
      </DocSection>

      <DocSection title="Cloud & Costs" {...sectionProps("costs")}>
        <DocSubheading>Cloud Mapping</DocSubheading>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Component</th>
                <th>Status</th>
                <th>AWS</th>
                <th>Google Cloud</th>
                <th>Azure</th>
              </tr>
            </thead>
            <tbody>
              {componentsWithCloud.map((c) => (
                <tr key={c.key + c.name} className={c.optional ? "row-optional" : ""}>
                  <td>
                    <strong>{c.name}</strong>
                  </td>
                  <td>
                    <span className={`badge ${c.optional ? "optional" : "required"}`}>
                      {c.optional ? "Optional" : "Required"}
                    </span>
                  </td>
                  <td>{formatCloudServices(c.cloud_mapping.aws)}</td>
                  <td>{formatCloudServices(c.cloud_mapping.gcp)}</td>
                  <td>{formatCloudServices(c.cloud_mapping.azure)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <DocSubheading>Cost Estimation</DocSubheading>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Provider</th>
                <th>Required / month</th>
                <th>Optional add-on</th>
                <th>Total (all selected)</th>
              </tr>
            </thead>
            <tbody>
              {costs.map((c) => (
                <tr key={c.provider}>
                  <td>
                    <strong>{PROVIDER_LABELS[c.provider] || c.provider}</strong>
                  </td>
                  <td>
                    ${c.requiredLow}–${c.requiredHigh}
                  </td>
                  <td>
                    {c.optionalHigh > 0 ? `+$${c.optionalLow}–$${c.optionalHigh}` : "—"}
                  </td>
                  <td>
                    ${c.totalLow}–${c.totalHigh}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="doc-footnote">
          Estimated ranges based on users, stage, and selected components — not exact billing.{" "}
          {hasOptionalCost
            ? "Moving components between Required and Optional updates these figures."
            : "Actual costs depend on real usage."}
        </p>
      </DocSection>
    </article>
  );
}
