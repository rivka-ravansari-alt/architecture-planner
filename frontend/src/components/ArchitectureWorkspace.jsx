import { useCallback, useEffect, useRef, useState } from "react";
import { DOCUMENT_SECTIONS } from "../architectureHelpers.js";
import ArchitectureDocument from "./architecture/ArchitectureDocument.jsx";

const DEFAULT_EXPANDED = Object.fromEntries(
  DOCUMENT_SECTIONS.map((s) => [s.id, true])
);

export default function ArchitectureWorkspace({
  project,
  projectTypes,
  components,
  onMove,
  risks,
  recommendations,
  costs,
  onExit,
  onReset,
  onToggleAppSidebar,
  appSidebarCollapsed,
}) {
  const [activeSection, setActiveSection] = useState("overview");
  const [expandedSections, setExpandedSections] = useState(DEFAULT_EXPANDED);
  const scrollRef = useRef(null);
  const sectionRefs = useRef({});

  const registerSection = useCallback((id, node) => {
    if (node) sectionRefs.current[id] = node;
  }, []);

  useEffect(() => {
    const root = scrollRef.current;
    if (!root) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]?.target?.id) {
          setActiveSection(visible[0].target.id);
        }
      },
      { root, rootMargin: "-20% 0px -55% 0px", threshold: [0, 0.25, 0.5, 1] }
    );

    for (const section of DOCUMENT_SECTIONS) {
      const node = sectionRefs.current[section.id];
      if (node) observer.observe(node);
    }

    return () => observer.disconnect();
  }, [expandedSections]);

  const scrollToSection = (id) => {
    setExpandedSections((prev) => ({ ...prev, [id]: true }));
    requestAnimationFrame(() => {
      const node = sectionRefs.current[id];
      if (node) {
        node.scrollIntoView({ behavior: "smooth", block: "start" });
        setActiveSection(id);
      }
    });
  };

  const toggleSection = (id) => {
    setExpandedSections((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="focus-workspace">
      <header className="focus-workspace-bar">
        <div className="focus-workspace-bar-start">
          <button type="button" className="focus-back-btn" onClick={onExit}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M19 12H5 M12 19l-7-7 7-7" />
            </svg>
            Back to project setup
          </button>
        </div>
        <div className="focus-workspace-bar-center">
          <h1 className="focus-workspace-title">Architecture Document</h1>
          <p className="focus-workspace-sub">{project.name}</p>
        </div>
        <div className="focus-workspace-bar-end">
          <button
            type="button"
            className="btn btn-ghost focus-sidebar-toggle"
            onClick={onToggleAppSidebar}
            title={appSidebarCollapsed ? "Show application menu" : "Hide application menu"}
          >
            {appSidebarCollapsed ? "Show menu" : "Hide menu"}
          </button>
          <button type="button" className="btn btn-ghost" onClick={onReset}>
            Reset project
          </button>
        </div>
      </header>

      <div className="arch-doc-shell">
        <aside className="arch-doc-toc" aria-label="Table of contents">
          <nav className="arch-doc-toc-list">
            {DOCUMENT_SECTIONS.map((section) => (
              <button
                key={section.id}
                type="button"
                className={`arch-doc-toc-item ${activeSection === section.id ? "active" : ""}`}
                onClick={() => scrollToSection(section.id)}
                aria-current={activeSection === section.id ? "location" : undefined}
              >
                {section.label}
              </button>
            ))}
          </nav>
        </aside>

        <div className="arch-doc-scroll" ref={scrollRef}>
          <div className="arch-doc-scroll-inner">
            <ArchitectureDocument
              project={project}
              projectTypes={projectTypes}
              components={components}
              onMove={onMove}
              risks={risks}
              recommendations={recommendations}
              costs={costs}
              expandedSections={expandedSections}
              onToggleSection={toggleSection}
              sectionRef={registerSection}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
