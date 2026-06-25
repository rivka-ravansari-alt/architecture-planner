import { useEffect, useRef } from "react";

import { DOCUMENT_SECTIONS } from "../../../constants/document.js";
import { STAGES } from "../../../constants/wizard.js";
import { useDocumentSections } from "../../../hooks/useDocumentSections.js";
import { labelFor } from "../../../utils/text.js";
import ArchitectureDocument from "./ArchitectureDocument.jsx";

export default function ArchitectureWorkspace({
  project,
  projectTypes,
  components,
  costs,
  hasPricing,
  canGeneratePricing,
  loading,
  onGeneratePricing,
  onExit,
  onReset,
  onToggleAppSidebar,
  appSidebarCollapsed,
}) {
  const {
    activeSection,
    expandedSections,
    scrollRef,
    registerSection,
    scrollToSection,
    toggleSection,
  } = useDocumentSections();

  const hadPricingRef = useRef(hasPricing);

  useEffect(() => {
    if (hasPricing && !hadPricingRef.current) {
      scrollToSection("costs");
    }
    hadPricingRef.current = hasPricing;
  }, [hasPricing, scrollToSection]);

  const handleGeneratePricing = async () => {
    const result = await onGeneratePricing();
    if (result) {
      scrollToSection("costs");
    }
  };

  return (
    <div className="focus-workspace">
      <header className="focus-workspace-bar">
        <div className="focus-workspace-bar-start">
          <button type="button" className="focus-back-btn" onClick={onExit}>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M19 12H5 M12 19l-7-7 7-7" />
            </svg>
            Back to component review
          </button>
        </div>
        <div className="focus-workspace-bar-center">
          <h1 className="focus-workspace-title">Architecture Document</h1>
          <p className="focus-workspace-sub">
            {project.name}
            <span className="focus-workspace-meta">
              · {labelFor(STAGES, project.stage)}
              {hasPricing ? " · Pricing generated" : canGeneratePricing ? " · Review architecture" : ""}
            </span>
          </p>
        </div>
        <div className="focus-workspace-bar-end">
          {canGeneratePricing && !hasPricing && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleGeneratePricing}
              disabled={loading}
            >
              {loading ? "Generating pricing…" : "Generate Pricing"}
            </button>
          )}
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
                {section.id === "costs" && !hasPricing && canGeneratePricing && (
                  <span className="arch-doc-toc-pending">Pending</span>
                )}
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
              costs={costs}
              hasPricing={hasPricing}
              canGeneratePricing={canGeneratePricing}
              loading={loading}
              onGeneratePricing={handleGeneratePricing}
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
