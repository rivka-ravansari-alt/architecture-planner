import DocSection from "./document/DocSection.jsx";
import OverviewSection from "./document/OverviewSection.jsx";
import ComponentsSection from "./document/ComponentsSection.jsx";
import RisksSection from "./document/RisksSection.jsx";
import CloudCostsSection from "./document/CloudCostsSection.jsx";
import { BulletList, ChecklistList, FlowList } from "./document/DocumentLists.jsx";
import ArchitectureDiagrams from "./diagrams/ArchitectureDiagrams.jsx";

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
}) {
  const indexed = components.map((component, index) => ({ ...component, _i: index }));
  const required = indexed.filter((component) => !component.optional);
  const optional = indexed.filter((component) => component.optional);

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
        <ComponentsSection required={required} optional={optional} onMove={onMove} />
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
        <RisksSection risks={risks} />
      </DocSection>

      <DocSection title="Recommendations" {...sectionProps("recommendations")}>
        <BulletList items={recommendations} emptyMessage="No recommendations at this time." />
      </DocSection>

      <DocSection title="Next Steps" {...sectionProps("next-steps")}>
        <ChecklistList items={project.next_steps} emptyMessage="No next steps defined." />
      </DocSection>

      <DocSection title="Cloud & Costs" {...sectionProps("costs")}>
        <CloudCostsSection components={components} costs={costs} />
      </DocSection>
    </article>
  );
}
