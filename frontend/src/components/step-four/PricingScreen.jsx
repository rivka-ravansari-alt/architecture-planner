import { Fragment, useCallback, useEffect, useRef, useState } from "react";

import { projectApi } from "../../api/projectApi.js";
import ErrorBanner from "../ui/ErrorBanner.jsx";
import { Spinner } from "../ui/Spinner.jsx";

const PROVIDER_ORDER = ["aws", "azure", "gcp"];

const STATUS_LABELS = {
  aws: "Calculating AWS pricing...",
  azure: "Calculating Azure pricing...",
  gcp: "Calculating Google Cloud pricing...",
};

const PROVIDER_LABELS = {
  aws: "AWS",
  azure: "Azure",
  gcp: "Google Cloud",
};

/**
 * @param {number|null|undefined} amount
 */
function formatCurrency(amount) {
  if (amount == null || Number.isNaN(amount)) {
    return "—";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * @param {{ item: import("../../api/projectApi.js").PricingLineItem }} props
 */
function PricingDetailsPanel({ item }) {
  const summary = Array.isArray(item.calculation_summary)
    ? item.calculation_summary
    : [];

  return (
    <div className="pricing-details-panel">
      <dl className="pricing-details-meta">
        <div>
          <dt>Component</dt>
          <dd>{item.component_name}</dd>
        </div>
        <div>
          <dt>Cloud service</dt>
          <dd>{item.service_name || "—"}</dd>
        </div>
        <div>
          <dt>Monthly price</dt>
          <dd>{formatCurrency(item.monthly_price)}</dd>
        </div>
      </dl>

      <section className="pricing-details-reason">
        <h4>Selection reason</h4>
        <p>
          {item.selection_reason ||
            "No selection reason was saved for this component."}
        </p>
      </section>

      <section className="pricing-details-summary">
        <h4>Calculation summary</h4>
        {summary.length > 0 ? (
          <ul>
            {summary.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        ) : (
          <p className="pricing-details-empty">
            No calculation summary available.
          </p>
        )}
      </section>
    </div>
  );
}

/**
 * @param {import("../../api/projectApi.js").ProviderPricingResult[]} providerResults
 */
function providerMapFromResults(providerResults) {
  return Object.fromEntries(providerResults.map((result) => [result.provider, result]));
}

/**
 * @param {import("../../api/projectApi.js").ProviderPricingResult[]} providerResults
 */
function isPricingComplete(providerResults) {
  return PROVIDER_ORDER.every((provider) => {
    const result = providerResults.find((entry) => entry.provider === provider);
    return result?.status === "completed" || result?.status === "failed";
  });
}

/**
 * Step 4: progressive per-provider cloud pricing.
 *
 * @param {{ projectId: string, onBack?: () => void }} props
 */
export default function PricingScreen({ projectId, onBack }) {
  const [providers, setProviders] = useState(
    /** @type {Record<string, import("../../api/projectApi.js").ProviderPricingResult>} */ ({})
  );
  const [activeProvider, setActiveProvider] = useState(null);
  const [comparison, setComparison] = useState(
    /** @type {import("../../api/projectApi.js").PricingComparisonRow[]} */ ([])
  );
  const [expandedDetails, setExpandedDetails] = useState(
    /** @type {Record<string, boolean>} */ ({})
  );
  const [phase, setPhase] = useState("preparing");
  const [error, setError] = useState("");
  const requestRef = useRef(0);
  const runIdRef = useRef(null);

  const allFinished =
    PROVIDER_ORDER.every((provider) => {
      const status = providers[provider]?.status;
      return status === "completed" || status === "failed";
    }) && PROVIDER_ORDER.some((provider) => providers[provider]);

  const ensureUsageModel = useCallback(async () => {
    try {
      await projectApi.getGlobalUsageModel(projectId);
    } catch (err) {
      const message = err.message || "";
      if (!message.includes("No global usage model exists")) {
        throw err;
      }
      await projectApi.generateGlobalUsageModel(projectId);
    }
  }, [projectId]);

  const runProgressivePricing = useCallback(
    async ({ existingRunId = null, initialProviders = {} } = {}) => {
    const requestId = ++requestRef.current;
    setPhase("pricing");
    setError("");
    setComparison([]);
    setActiveProvider(null);
    setExpandedDetails({});
    runIdRef.current = existingRunId;
    setProviders(existingRunId ? initialProviders : {});

    try {
      await ensureUsageModel();
      if (requestId !== requestRef.current) return;

      const completedProviders = new Set(
        Object.values(initialProviders)
          .filter((result) => result.status === "completed" || result.status === "failed")
          .map((result) => result.provider)
      );

      for (const provider of PROVIDER_ORDER) {
        if (requestId !== requestRef.current) return;
        if (existingRunId && completedProviders.has(provider)) {
          continue;
        }

        setActiveProvider(provider);
        setProviders((prev) => ({
          ...prev,
          [provider]: {
            provider,
            provider_label: PROVIDER_LABELS[provider],
            status: "calculating",
            line_items: [],
            monthly_total: 0,
          },
        }));

        try {
          const response = await projectApi.generateProviderPricing(
            projectId,
            provider,
            runIdRef.current
          );
          if (requestId !== requestRef.current) return;

          runIdRef.current = response.run_id;
          setProviders((prev) => ({
            ...prev,
            [provider]: response.result,
          }));
        } catch (err) {
          if (requestId !== requestRef.current) return;

          setProviders((prev) => ({
            ...prev,
            [provider]: {
              provider,
              provider_label: PROVIDER_LABELS[provider],
              status: "failed",
              line_items: [],
              monthly_total: 0,
              error: err.message || `Could not calculate ${PROVIDER_LABELS[provider]} pricing.`,
            },
          }));
        }
      }

      if (requestId !== requestRef.current || !runIdRef.current) return;

      const latest = await projectApi.getPricingRun(projectId, runIdRef.current);
      if (requestId !== requestRef.current) return;

      setComparison(latest.comparison);
      setProviders(providerMapFromResults(latest.providers));
    } catch (err) {
      if (requestId !== requestRef.current) return;
      setError(err.message || "Could not calculate pricing. Please try again.");
    } finally {
      if (requestId === requestRef.current) {
        setActiveProvider(null);
        setPhase("done");
      }
    }
  },
  [projectId, ensureUsageModel]);

  useEffect(() => {
    let active = true;

    (async () => {
      setPhase("preparing");
      setError("");
      setProviders({});
      setComparison([]);
      setExpandedDetails({});
      runIdRef.current = null;
      try {
        await ensureUsageModel();
        if (!active) return;

        try {
          const existing = await projectApi.getLatestPricing(projectId);
          if (!active) return;

          runIdRef.current = existing.run_id;
          setProviders(providerMapFromResults(existing.providers));
          setComparison(existing.comparison);

          if (!isPricingComplete(existing.providers)) {
            await runProgressivePricing({
              existingRunId: existing.run_id,
              initialProviders: providerMapFromResults(existing.providers),
            });
          } else {
            setPhase("done");
          }
        } catch (loadErr) {
          if (!active) return;
          const message = loadErr.message || "";
          if (!message.includes("No pricing run exists")) {
            setError(message || "Could not load pricing.");
            setPhase("done");
            return;
          }
          await runProgressivePricing();
        }
      } catch (err) {
        if (!active) return;
        setError(err.message || "Could not prepare pricing. Please try again.");
        setPhase("done");
      }
    })();

    return () => {
      active = false;
      requestRef.current += 1;
    };
  }, [projectId, ensureUsageModel, runProgressivePricing]);

  /**
   * @param {string} provider
   * @param {string} instanceId
   */
  function toggleDetails(provider, instanceId) {
    const key = `${provider}:${instanceId}`;
    setExpandedDetails((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  }

  if (phase === "preparing") {
    return (
      <div className="pricing-loading">
        <Spinner />
        <p>Preparing usage model and pricing…</p>
      </div>
    );
  }

  return (
    <div className="pricing-screen">
      <header className="pricing-header">
        <h1>Cloud pricing</h1>
        <p className="subtitle">
          Estimated monthly costs per provider, calculated progressively.
        </p>
      </header>

      {error && <ErrorBanner message={error} />}

      {activeProvider && (
        <p className="pricing-status" role="status">
          {STATUS_LABELS[activeProvider]}
        </p>
      )}

      <div className="pricing-providers">
        {PROVIDER_ORDER.map((provider) => {
          const result = providers[provider];
          const label = result?.provider_label || PROVIDER_LABELS[provider];
          const isCalculating =
            result?.status === "calculating" || activeProvider === provider;

          return (
            <section key={provider} className="pricing-provider-section">
              <h2>{label}</h2>

              {isCalculating && (
                <div className="pricing-provider-loading">
                  <Spinner />
                  <p>{STATUS_LABELS[provider]}</p>
                </div>
              )}

              {result?.status === "failed" && (
                <ErrorBanner
                  message={result.error || `Could not calculate ${label} pricing.`}
                />
              )}

              {result?.status === "completed" && (
                <>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Component</th>
                          <th>Service</th>
                          <th>Status</th>
                          <th>Monthly price</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.line_items.map((item) => {
                          const detailsKey = `${provider}:${item.instance_id}`;
                          const isExpanded = Boolean(expandedDetails[detailsKey]);
                          const canShowDetails = item.status === "priced";

                          return (
                            <Fragment key={item.instance_id}>
                              <tr
                                className={
                                  item.status === "skipped" || item.status === "failed"
                                    ? "pricing-row-unpriced"
                                    : undefined
                                }
                              >
                                <td>
                                  <strong>{item.component_name}</strong>
                                </td>
                                <td>{item.service_name || "—"}</td>
                                <td>
                                  {item.status === "priced" && "Priced"}
                                  {item.status === "skipped" && "Not priced"}
                                  {item.status === "failed" && "Failed"}
                                  {!item.status && "Priced"}
                                  {item.skip_reason && (
                                    <p className="pricing-skip-reason">{item.skip_reason}</p>
                                  )}
                                </td>
                                <td>{formatCurrency(item.monthly_price)}</td>
                                <td>
                                  {canShowDetails ? (
                                    <button
                                      type="button"
                                      className="btn btn-ghost pricing-details-toggle"
                                      aria-expanded={isExpanded}
                                      onClick={() =>
                                        toggleDetails(provider, item.instance_id)
                                      }
                                    >
                                      {isExpanded ? "Hide details" : "Details"}
                                    </button>
                                  ) : (
                                    <span className="pricing-details-unavailable">—</span>
                                  )}
                                </td>
                              </tr>
                              {canShowDetails && isExpanded && (
                                <tr className="pricing-details-row">
                                  <td colSpan={5}>
                                    <PricingDetailsPanel item={item} />
                                  </td>
                                </tr>
                              )}
                            </Fragment>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  <p className="pricing-provider-total">
                    <span>{label} total</span>
                    <strong>{formatCurrency(result.monthly_total)}</strong>
                  </p>
                </>
              )}

              {!result && !isCalculating && (
                <p className="pricing-provider-pending">Waiting to calculate…</p>
              )}
            </section>
          );
        })}
      </div>

      {allFinished && comparison.length > 0 && (
        <section className="pricing-comparison">
          <h2>Provider comparison</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>Monthly total</th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((row) => (
                  <tr key={row.provider}>
                    <td>
                      <strong>{row.provider_label}</strong>
                    </td>
                    <td>
                      {row.status === "completed"
                        ? formatCurrency(row.monthly_total)
                        : row.status === "failed"
                          ? "Failed"
                          : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {onBack && (
        <div className="actions">
          <button type="button" className="btn btn-ghost" onClick={onBack}>
            Back
          </button>
        </div>
      )}
    </div>
  );
}
