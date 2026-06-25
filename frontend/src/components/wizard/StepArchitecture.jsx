import ArchitectureDiagrams from "../../features/architecture/components/diagrams/ArchitectureDiagrams.jsx";
import { FlowList } from "../../features/architecture/components/document/DocumentLists.jsx";

export default function StepArchitecture({ project, components }) {
  const hasDiagrams = Boolean(project?.architecture_diagrams);

  return (
    <section className="panel panel-wide">
      <div className="wizard-architecture-body">
        <div className="wizard-architecture-section">
          <h3 className="wizard-section-title">Architecture Diagrams</h3>
          <p className="wizard-section-sub">
            {hasDiagrams
              ? "Switch between the high-level design and system flow views using the tabs below."
              : "Generate architecture diagrams to visualize your design, or skip this step to continue to pricing."}
          </p>
          {hasDiagrams ? (
            <ArchitectureDiagrams project={project} components={components} />
          ) : null}
        </div>

        {hasDiagrams ? (
          <div className="wizard-architecture-section">
            <h3 className="wizard-section-title">Architecture Flow</h3>
            <FlowList
              steps={project?.main_flow}
              emptyMessage="No architecture flow steps available."
            />
          </div>
        ) : null}
      </div>
    </section>
  );
}