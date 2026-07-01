import DocSection from "./document/DocSection.jsx";
import OverviewSection from "./document/OverviewSection.jsx";
import ComponentsSection from "./document/ComponentsSection.jsx";
import CloudCostsSection from "./document/CloudCostsSection.jsx";
import { FlowList } from "./document/DocumentLists.jsx";
import ArchitectureDiagrams from "./diagrams/ArchitectureDiagrams.jsx";
import { partitionIndexedComponents } from "../../../utils/components.js";

export default function ArchitectureDocument({
  project,
  projectTypes,
  components,
  onMove = null,
  costs,
  hasPricing,
  expandedSections,
  onToggleSection,
  sectionRef,
}) {
  const { required, optional } = partitionIndexedComponents(components);

  const sectionProps = (id) => ({
    id,
    sectionRef,
    expanded: expandedSections[id] !== false,
    onToggle: () => onToggleSection(id),
  });

  return (
    <article className="arch-doc-content">
      <DocSection title="Overview" {...sectionProps("overview")}>
        <OverviewSection
          project={project}
          projectTypes={projectTypes}
          requiredCount={required.length}
          optionalCount={optional.length}
        />
      </DocSection>

      <DocSection title="Components" {...sectionProps("components")}>
        <ComponentsSection
          required={required}
          optional={optional}
          onMove={onMove}
          readOnly={!onMove}
        />
      </DocSection>

      <DocSection title="Architecture Diagrams" {...sectionProps("diagrams")}>
        <p className="doc-text doc-diagram-intro">
          Switch between the high-level design and system flow views using the tabs in the
          diagram workspace below.
        </p>
        <ArchitectureDiagrams project={project} components={components} />
      </DocSection>

      <DocSection title="Architecture Flow" {...sectionProps("flow")}>
        <FlowList steps={project.main_flow} emptyMessage="No architecture flow steps available." />
      </DocSection>

      <DocSection
        title="Cloud & Costs"
        {...sectionProps("costs")}
        badge={hasPricing ? null : "Pending"}
      >
        {(costs?.length ?? 0) > 0 ? (
          <CloudCostsSection components={components} costs={costs} />
        ) : (
          <p className="muted doc-empty">
            Complete architecture generation to see cloud cost estimates.
          </p>
        )}
      </DocSection>
    </article>
  );
}
