export default function DocSection({ id, title, expanded, onToggle, sectionRef, children }) {
  return (
    <section className="arch-doc-section" id={id} ref={(node) => sectionRef?.(id, node)}>
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
