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
