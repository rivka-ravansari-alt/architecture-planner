export function FlowList({ steps, emptyMessage }) {
  if (!steps?.length) {
    return emptyMessage ? <p className="muted doc-empty">{emptyMessage}</p> : null;
  }
  return (
    <ol className="flow-list">
      {steps.map((step, index) => (
        <li key={index}>{step}</li>
      ))}
    </ol>
  );
}

export function BulletList({ items, emptyMessage }) {
  if (!items?.length) {
    return emptyMessage ? <p className="muted doc-empty">{emptyMessage}</p> : null;
  }
  return (
    <ul className="doc-bullet-list">
      {items.map((item, index) => (
        <li key={index}>{item}</li>
      ))}
    </ul>
  );
}

export function ChecklistList({ items, emptyMessage }) {
  if (!items?.length) {
    return emptyMessage ? <p className="muted doc-empty">{emptyMessage}</p> : null;
  }
  return (
    <ul className="checklist-list">
      {items.map((item, index) => (
        <li key={index} className="checklist-item">
          <span className="checklist-marker" aria-hidden="true" />
          <span className="checklist-text">{item}</span>
        </li>
      ))}
    </ul>
  );
}
