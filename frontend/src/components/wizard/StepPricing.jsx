import CloudCostsSection from "../../features/architecture/components/document/CloudCostsSection.jsx";

export default function StepPricing({ components, costs, hasPricing }) {
  return (
    <section className="panel panel-wide">
      <div className="wizard-pricing-body">
        {hasPricing ? (
          <CloudCostsSection components={components} costs={costs} />
        ) : (
          <p className="muted doc-empty">
            Generate pricing from the Architecture step to see cloud cost estimates here.
          </p>
        )}
      </div>
    </section>
  );
}
