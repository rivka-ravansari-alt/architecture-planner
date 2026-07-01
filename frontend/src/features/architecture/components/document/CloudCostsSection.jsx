import Badge from "../../../../components/ui/Badge.jsx";

import { isPricedBreakdownRow } from "../../../../constants/costs.js";

import { PROVIDER_LABELS } from "../../../../constants/providers.js";

import { formatCloudServices } from "../../../../utils/text.js";

import DocSubheading from "./DocSubheading.jsx";



function formatMoney(value) {

  if (value == null || Number.isNaN(value)) return "—";

  return `$${Number(value).toFixed(2)}`;

}



function formatProviderCostRange(cost) {

  if (cost.requiredLow == null || cost.requiredHigh == null) {

    return "Not priced";

  }

  return `$${cost.requiredLow}–$${cost.requiredHigh}`;

}



function formatOptionalCostRange(cost) {

  if (cost.optionalHigh == null || cost.optionalHigh <= 0) {

    return "—";

  }

  return `+$${cost.optionalLow}–$${cost.optionalHigh}`;

}



function formatComponentCost(item) {

  if (!isPricedBreakdownRow(item)) {

    return "Not priced";

  }

  return formatMoney(item.component_monthly_cost ?? item.final_component_cost);

}



export default function CloudCostsSection({ components, costs }) {
  const componentsWithCloud = components.filter((component) => component.cloud_mapping);
  const hasOptionalCost = costs.some((cost) => (cost.optionalHigh ?? 0) > 0);
  const hasUnknownOnly =
    costs.length > 0 &&
    costs.every((cost) => (cost.pricingDebugTable?.length ?? 0) === 0) &&
    costs.some((cost) => (cost.unknownItems?.length ?? 0) > 0);
  const debugRows = costs.flatMap((cost) =>

    (cost.pricingDebugTable ?? cost.componentBreakdown ?? []).map((row) => ({

      ...row,

      provider: row.provider || cost.provider,

    })),

  );



  return (

    <>

      {hasUnknownOnly ? (
        <p className="doc-footnote cost-stale-notice">
          No component costs could be calculated. Check warnings below — this usually means missing
          pricing profiles or catalog SKUs in Firestore for the selected cloud services.
        </p>
      ) : null}

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

              <tr key={component.key + component.name} className={component.optional ? "row-optional" : ""}>

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



      <DocSubheading>Cost Estimation</DocSubheading>

      <div className="table-wrap">

        <table>

          <thead>

            <tr>

              <th>Provider</th>

              <th>Required / month</th>

              <th>Optional add-on</th>

            </tr>

          </thead>

          <tbody>

            {costs.map((cost) => (

              <tr key={cost.provider}>

                <td>

                  <strong>{PROVIDER_LABELS[cost.provider] || cost.provider}</strong>

                </td>

                <td>{formatProviderCostRange(cost)}</td>

                <td>{formatOptionalCostRange(cost)}</td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

      <p className="doc-footnote">

        Required totals include required components only. Optional add-ons are priced separately.{" "}

        {costs.some((cost) => cost.unknownItems?.length) ? (

          <>Some services were excluded or had no pricing match; see debug table. </>

        ) : null}

        {costs.some((cost) => cost.warnings?.length) ? (

          <>Review cost warnings in the pricing debug table. </>

        ) : null}

        {hasOptionalCost

          ? "Moving components between Required and Optional updates these figures."

          : "Actual costs depend on real usage."}

      </p>



      {debugRows.length > 0 ? (

        <>

          <DocSubheading>Pricing Debug Table</DocSubheading>

          <div className="table-wrap">

            <table>

              <thead>

                <tr>

                  <th>Provider</th>

                  <th>Component</th>

                  <th>Type</th>

                  <th>Status</th>

                  <th>Service</th>

                  <th>Profile</th>

                  <th>Model</th>

                  <th>Cost/mo</th>

                  <th>In total?</th>

                  <th>SKU role</th>

                  <th>SKU name</th>

                  <th>Unit</th>

                  <th>Unit price</th>

                  <th>Quantity</th>

                  <th>Line cost</th>

                </tr>

              </thead>

              <tbody>

                {debugRows.flatMap((item) => {

                  const skuLines = item.sku_lines?.length ? item.sku_lines : [null];

                  return skuLines.map((line, index) => (

                    <tr

                      key={`${item.provider}-${item.component_key}-${line?.sku_role ?? "none"}-${index}`}

                      className={

                        item.included_in_total === false || !isPricedBreakdownRow(item)

                          ? "row-excluded-cost"

                          : ""

                      }

                    >

                      <td>{index === 0 ? PROVIDER_LABELS[item.provider] || item.provider : ""}</td>

                      <td>{index === 0 ? item.component_name : ""}</td>

                      <td>{index === 0 ? item.component_type : ""}</td>

                      <td>{index === 0 ? (item.status || (item.optional ? "optional" : "required")) : ""}</td>

                      <td>{index === 0 ? item.selected_cloud_service : ""}</td>

                      <td>{index === 0 ? (item.pricing_profile_id || "Not priced") : ""}</td>

                      <td>{index === 0 ? item.pricing_model : ""}</td>

                      <td>{index === 0 ? formatComponentCost(item) : ""}</td>

                      <td>

                        {index === 0

                          ? item.included_in_total === false

                            ? `No (${item.exclusion_reason || "excluded"})`

                            : isPricedBreakdownRow(item)

                              ? "Yes"

                              : "No (no profile)"

                          : ""}

                      </td>

                      <td>{line?.sku_role || "—"}</td>

                      <td>{line?.sku_name || line?.sku_id || "—"}</td>

                      <td>{line?.usage_unit || "—"}</td>

                      <td>{line?.unit_price != null ? formatMoney(line.unit_price) : "—"}</td>

                      <td title={line?.quantity_note}>{line?.calculated_quantity ?? "—"}</td>

                      <td>{line ? formatMoney(line.line_item_cost) : "—"}</td>

                    </tr>

                  ));

                })}

              </tbody>

            </table>

          </div>

        </>

      ) : null}



      {costs.some((cost) => cost.warnings?.length || cost.unknownItems?.length) ? (

        <>

          <DocSubheading>Warnings & Excluded Items</DocSubheading>

          {costs.map((cost) =>

            cost.warnings?.length || cost.unknownItems?.length ? (

              <details key={cost.provider} className="cost-audit-details">

                <summary>

                  <strong>{PROVIDER_LABELS[cost.provider] || cost.provider}</strong>

                </summary>

                {cost.unknownItems?.length ? (

                  <ul className="cost-audit-warnings">

                    {cost.unknownItems.map((item) => (

                      <li key={item}>{item}</li>

                    ))}

                  </ul>

                ) : null}

                {cost.warnings?.length ? (

                  <ul className="cost-audit-warnings">

                    {cost.warnings.map((warning) => (

                      <li key={warning}>{warning}</li>

                    ))}

                  </ul>

                ) : null}

              </details>

            ) : null,

          )}

        </>

      ) : null}

    </>

  );

}
