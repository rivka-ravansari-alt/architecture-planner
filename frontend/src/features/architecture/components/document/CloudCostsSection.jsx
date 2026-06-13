import Badge from "../../../../components/ui/Badge.jsx";
import { PROVIDER_LABELS } from "../../../../constants/providers.js";
import { formatCloudServices } from "../../../../utils/text.js";
import DocSubheading from "./DocSubheading.jsx";

const INFRASTRUCTURE_CATEGORY_ORDER = [
  "compute",
  "database",
  "storage",
  "api_gateway",
  "load_balancer",
  "cdn",
  "queue",
  "cache",
  "search",
  "monitoring",
  "logging",
  "tracing",
  "alerting",
  "secrets",
  "backups",
];

const INFRASTRUCTURE_CATEGORY_LABELS = {
  infrastructure_summary: "Infrastructure (summary — regenerate for category detail)",
  compute: "Compute",
  database: "Database",
  storage: "Object storage",
  api_gateway: "API gateway",
  load_balancer: "Load balancer",
  cdn: "CDN",
  queue: "Queue",
  cache: "Cache",
  search: "Search",
  monitoring: "Monitoring",
  logging: "Logging",
  tracing: "Tracing",
  alerting: "Alerting",
  secrets: "Secrets",
  backups: "Backups",
};

const CONFIDENCE_LABELS = {
  low: "Low confidence",
  medium: "Medium confidence",
  high: "High confidence",
};

const CLOUD_PROVIDERS = ["aws", "gcp", "azure"];

function formatRange(range) {
  if (!range || (range.low === 0 && range.high === 0)) return "—";
  return `$${range.low}–$${range.high}`;
}

function orderedCategoryKeys(categories) {
  if (!categories) return [];
  const keys = Object.keys(categories);
  return [
    ...INFRASTRUCTURE_CATEGORY_ORDER.filter((key) => keys.includes(key)),
    ...keys.filter((key) => !INFRASTRUCTURE_CATEGORY_ORDER.includes(key)),
  ];
}

function resolveInfrastructureView(costs) {
  const cloudInfra = costs?.cloud_infrastructure;
  const categories = cloudInfra?.categories ?? {};
  let categoryKeys = orderedCategoryKeys(categories);

  const providerTotals = cloudInfra?.provider_totals ?? costs?.cloud_cost ?? {};
  const hasProviderTotals = CLOUD_PROVIDERS.some(
    (provider) => (providerTotals[provider]?.low ?? 0) > 0 || (providerTotals[provider]?.high ?? 0) > 0
  );

  const isLegacySummary = categoryKeys.length === 0 && hasProviderTotals;
  if (isLegacySummary) {
    categoryKeys = ["infrastructure_summary"];
  }

  return { cloudInfra, categoryKeys, providerTotals, hasProviderTotals, isLegacySummary };
}

function getCategoryMatrix(costs, cloudInfra, categoryKey) {
  if (categoryKey === "infrastructure_summary") {
    return costs?.cloud_cost ?? cloudInfra?.provider_totals ?? {};
  }
  return cloudInfra?.categories?.[categoryKey];
}

function getProviderRange(matrix, provider) {
  return matrix?.[provider] ?? matrix?.[provider.toLowerCase()] ?? null;
}

export default function CloudCostsSection({ components, costs }) {
  const componentsWithCloud = components.filter((component) => component.cloud_mapping);
  const { cloudInfra, categoryKeys, providerTotals, hasProviderTotals, isLegacySummary } =
    resolveInfrastructureView(costs);
  const hasCategoryRows = categoryKeys.length > 0;

  const roughAi = costs?.ai_services_cost?.ai_services;
  const roughExternal = costs?.external_services_cost?.external_services;
  const hasRoughOther = Boolean(roughAi || roughExternal);

  return (
    <>
      <DocSubheading>Cloud Infrastructure Cost</DocSubheading>
      <p className="doc-text doc-cost-intro">
        Monthly infrastructure estimate by category — compare AWS, Google Cloud, and Azure side by
        side.
      </p>

      {costs?.confidence && (
        <p className="doc-text doc-cost-confidence">
          Estimation confidence:{" "}
          <Badge variant="neutral">
            {CONFIDENCE_LABELS[costs.confidence] || costs.confidence}
          </Badge>
        </p>
      )}

      {isLegacySummary && (
        <p className="doc-text doc-cost-secondary">
          This project was generated before detailed category breakdown was available. Regenerate
          architecture to see compute, database, storage, and other line items.
        </p>
      )}

      <div className="table-wrap table-wrap-primary">
        <table className="cloud-infra-cost-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>{PROVIDER_LABELS.aws}</th>
              <th>{PROVIDER_LABELS.gcp}</th>
              <th>{PROVIDER_LABELS.azure}</th>
            </tr>
          </thead>
          <tbody>
            {!hasCategoryRows && !hasProviderTotals ? (
              <tr>
                <td colSpan={4}>No cloud infrastructure costs estimated yet.</td>
              </tr>
            ) : (
              categoryKeys.map((categoryKey) => {
                const matrix = getCategoryMatrix(costs, cloudInfra, categoryKey);
                return (
                  <tr key={categoryKey}>
                    <td>
                      <strong>
                        {INFRASTRUCTURE_CATEGORY_LABELS[categoryKey] || categoryKey}
                      </strong>
                    </td>
                    {CLOUD_PROVIDERS.map((provider) => (
                      <td key={provider}>{formatRange(getProviderRange(matrix, provider))}</td>
                    ))}
                  </tr>
                );
              })
            )}
            {(hasCategoryRows || hasProviderTotals) && (
              <tr className="row-total">
                <td>
                  <strong>Provider total / month</strong>
                </td>
                {CLOUD_PROVIDERS.map((provider) => (
                  <td key={provider}>
                    <strong>{formatRange(providerTotals[provider])}</strong>
                  </td>
                ))}
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {hasRoughOther && (
        <>
          <DocSubheading>Other services (rough estimate)</DocSubheading>
          <p className="doc-text doc-cost-secondary">
            AI, payment, notification, and third-party API costs are not yet modeled in detail.
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Estimated / month</th>
                </tr>
              </thead>
              <tbody>
                {roughAi && (
                  <tr>
                    <td>AI services</td>
                    <td>{formatRange(roughAi)}</td>
                  </tr>
                )}
                {roughExternal && (
                  <tr>
                    <td>External services</td>
                    <td>{formatRange(roughExternal)}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

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
            {componentsWithCloud.map((component) => (
              <tr
                key={component.key + component.name}
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
                <td>{formatCloudServices(component.cloud_mapping.aws)}</td>
                <td>{formatCloudServices(component.cloud_mapping.gcp)}</td>
                <td>{formatCloudServices(component.cloud_mapping.azure)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {costs?.assumptions?.length > 0 && (
        <>
          <DocSubheading>Assumptions</DocSubheading>
          <ul className="doc-list">
            {costs.assumptions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}

      {costs?.unknown_items?.length > 0 && (
        <>
          <DocSubheading>Not included / unknown</DocSubheading>
          <ul className="doc-list">
            {costs.unknown_items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}

      {costs?.disclaimer && <p className="doc-footnote">{costs.disclaimer}</p>}
    </>
  );
}
