import Badge from "../../../../components/ui/Badge.jsx";
import { PROVIDER_LABELS } from "../../../../constants/providers.js";
import { normalizeCloudMappings } from "../../../../utils/cloudMappings.js";
import { formatCloudServices } from "../../../../utils/text.js";
import {
  formatCostRange,
  formatOptionalCostRange,
} from "../../utils/pricingDetailView.js";
import DocSubheading from "./DocSubheading.jsx";

export default function CloudCostsSection({ components = [], costs = [] }) {
  const componentsWithCloud = components.filter(
    (component) => component.cloud_mappings || component.cloud_mapping
  );
  const hasOptionalCost = costs.some((cost) => (cost.optionalHigh ?? 0) > 0);

  if (!componentsWithCloud.length && !costs.length) {
    return null;
  }

  return (
    <section className="doc-section cloud-costs-section">
      <DocSubheading>Cloud Costs</DocSubheading>
      {costs.length ? (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Cloud</th>
                  <th>Required / month</th>
                  <th>Optional add-on</th>
                  <th>Total / month</th>
                </tr>
              </thead>
              <tbody>
                {costs.map((cost) => (
                  <tr key={cost.provider}>
                    <td>
                      <strong>{PROVIDER_LABELS[cost.provider] ?? cost.provider}</strong>
                    </td>
                    <td>{formatCostRange(cost.requiredLow, cost.requiredHigh)}</td>
                    <td>{formatOptionalCostRange(cost.optionalLow, cost.optionalHigh)}</td>
                    <td>
                      <strong>{formatCostRange(cost.totalLow, cost.totalHigh)}</strong>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="doc-footnote">
            Estimated monthly costs based on your architecture and inferred usage — not exact
            billing.{" "}
            {hasOptionalCost
              ? "Optional add-ons apply when those components are enabled."
              : "All listed components are required."}
          </p>
        </>
      ) : (
        <p className="doc-footnote">No cost estimates available yet.</p>
      )}

      {componentsWithCloud.length ? (
        <>
          <DocSubheading>Cloud Service Mappings</DocSubheading>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Component</th>
                  <th>Status</th>
                  <th>AWS</th>
                  <th>Google Cloud</th>
                  <th>Azure</th>
                </tr>
              </thead>
              <tbody>
                {componentsWithCloud.map((component) => {
                  const mappings = normalizeCloudMappings(
                    component.cloud_mappings ?? component.cloud_mapping
                  );
                  return (
                    <tr
                      key={component.key ?? component.id}
                      className={component.optional ? "row-optional" : ""}
                    >
                      <td>
                        <strong>{component.name}</strong>
                      </td>
                      <td>
                        <Badge variant={component.optional ? "optional" : "required"}>
                          {component.optional ? "Optional" : "Required"}
                        </Badge>
                      </td>
                      <td>{formatCloudServices(mappings.aws)}</td>
                      <td>{formatCloudServices(mappings.gcp)}</td>
                      <td>{formatCloudServices(mappings.azure)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </section>
  );
}
