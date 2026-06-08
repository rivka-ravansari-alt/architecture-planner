import {
  getImplementationOptionEntries,
  IMPLEMENTATION_MODEL_LABELS,
} from "../../../../constants/implementationModels.js";

function OptionPoints({ label, items }) {
  if (!items?.length) return null;

  return (
    <div className="doc-implementation-points">
      <span className="doc-implementation-points-label">{label}</span>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function ImplementationOption({ entry }) {
  const { label, detail } = entry;

  if (detail.not_applicable) {
    return (
      <section className="doc-implementation-option is-na">
        <h5 className="doc-implementation-option-title">{label}</h5>
        <p className="doc-implementation-na">{detail.when_to_use}</p>
      </section>
    );
  }

  return (
    <section className="doc-implementation-option">
      <h5 className="doc-implementation-option-title">{label}</h5>
      <dl className="doc-implementation-meta">
        <div>
          <dt>When to use</dt>
          <dd>{detail.when_to_use}</dd>
        </div>
        {detail.cost_impact ? (
          <div>
            <dt>Cost impact</dt>
            <dd>{detail.cost_impact}</dd>
          </div>
        ) : null}
      </dl>
      <OptionPoints label="Pros" items={detail.pros} />
      <OptionPoints label="Cons" items={detail.cons} />
    </section>
  );
}

export default function ImplementationOptionsDetails({ implementationOptions }) {
  const entries = getImplementationOptionEntries(implementationOptions);
  if (!entries.length) return null;

  return (
    <details className="doc-implementation-details">
      <summary>Compare implementation options</summary>
      <div className="doc-implementation-options">
        {entries.map((entry) => (
          <ImplementationOption key={entry.key} entry={entry} />
        ))}
      </div>
    </details>
  );
}
