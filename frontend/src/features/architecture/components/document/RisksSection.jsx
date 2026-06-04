import { RISK_LEVELS } from "../../../../constants/document.js";
import { groupRisksBySeverity } from "../../../../utils/text.js";
import DocSubheading from "./DocSubheading.jsx";
import RiskCard from "./RiskCard.jsx";

export default function RisksSection({ risks }) {
  const riskGroups = groupRisksBySeverity(risks);

  return (
    <>
      {RISK_LEVELS.map((level) => {
        const items = riskGroups[level];
        if (items.length === 0) return null;
        return (
          <div key={level} className="doc-risk-group">
            <DocSubheading>{level.charAt(0).toUpperCase() + level.slice(1)} Severity</DocSubheading>
            <div className="doc-risk-grid">
              {items.map((risk, index) => (
                <RiskCard key={`${level}-${index}`} risk={risk} />
              ))}
            </div>
          </div>
        );
      })}
      {risks.length === 0 && <p className="muted doc-empty">No notable risks identified.</p>}
    </>
  );
}
