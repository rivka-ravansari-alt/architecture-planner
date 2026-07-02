import Badge from "../../../../components/ui/Badge.jsx";
import { PROVIDER_LABELS } from "../../../../constants/providers.js";
import { normalizeCloudMappings } from "../../../../utils/cloudMappings.js";
import { formatCloudServices } from "../../../../utils/text.js";
import DocSubheading from "./DocSubheading.jsx";

export default function CloudCostsSection({ components, costs }) {
  const componentsWithCloud = components.filter(
    (component) => component.cloud_mappings || component.cloud_mapping
  );
  const hasOptionalCost = costs.some((cost) => cost.optionalHigh > 0);

  return (
    <>
      <DocSubheading>Cloud Mapping</DocSubheading>
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
              const cloudMappings = normalizeCloudMappings(component);

              return (
                <tr key={component.key + component.name} className={component.optional ? "row-optional" : ""}>
                  <td>
                    <strong>{component.name}</strong>
                  </td>
                  <td>
                    <Badge variant={component.optional ? "optional" : "required"}>
                      {component.optional ? "Optional" : "Required"}
                    </Badge>
                  </td>
                  <td>{formatCloudServices(cloudMappings.aws)}</td>
                  <td>{formatCloudServices(cloudMappings.gcp)}</td>
                  <td>{formatCloudServices(cloudMappings.azure)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <DocSubheading>Cost Estimation</DocSubheading>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Provider</th>
              <th>Required / month</th>
              <th>Optional add-on</th>
              <th>Total (all selected)</th>
            </tr>
          </thead>
          <tbody>
            {costs.map((cost) => (
              <tr key={cost.provider}>
                <td>
                  <strong>{PROVIDER_LABELS[cost.provider] || cost.provider}</strong>
                </td>
                <td>
                  ${cost.requiredLow}–${cost.requiredHigh}
                </td>
                <td>{cost.optionalHigh > 0 ? `+$${cost.optionalLow}–$${cost.optionalHigh}` : "—"}</td>
                <td>
                  ${cost.totalLow}–${cost.totalHigh}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="doc-footnote">
        Estimated ranges based on users, stage, and selected components — not exact billing.{" "}
        {hasOptionalCost
          ? "Moving components between Required and Optional updates these figures."
          : "Actual costs depend on real usage."}
      </p>
    </>
  );
}
