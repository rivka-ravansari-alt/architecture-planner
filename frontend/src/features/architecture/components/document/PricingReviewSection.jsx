import { Spinner } from "../../../../components/ui/Spinner.jsx";
import { PROVIDER_LABELS } from "../../../../constants/providers.js";
import DocSubheading from "./DocSubheading.jsx";

export default function PricingReviewSection({ loading, onGeneratePricing }) {
  return (
    <div className="pricing-review-panel">
      <DocSubheading>Ready for pricing</DocSubheading>
      <p className="doc-text">
        Your architecture diagrams and approved components are saved. Generate monthly cost
        estimates for AWS, Google Cloud, and Azure using the existing pricing engine. This step
        does not regenerate components or diagrams.
      </p>
      <ul className="pricing-review-providers">
        {["aws", "gcp", "azure"].map((provider) => (
          <li key={provider}>{PROVIDER_LABELS[provider] || provider}</li>
        ))}
      </ul>
      <button
        type="button"
        className="btn btn-primary pricing-review-cta"
        onClick={onGeneratePricing}
        disabled={loading}
      >
        {loading && <Spinner />}
        {loading ? "Generating pricing…" : "Generate Pricing"}
      </button>
    </div>
  );
}
