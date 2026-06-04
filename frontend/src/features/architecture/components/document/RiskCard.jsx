import { truncateToSentences } from "../../../../utils/text.js";

export default function RiskCard({ risk }) {
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
