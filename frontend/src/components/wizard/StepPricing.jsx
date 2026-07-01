import CloudCostsSection from "../../features/architecture/components/document/CloudCostsSection.jsx";

export default function StepPricing({ components, costs }) {
  const showCosts = (costs?.length ?? 0) > 0;

  return (
    <section className="panel panel-wide">
      <div className="wizard-pricing-body">
        {showCosts ? (
          <CloudCostsSection components={components} costs={costs} />
        ) : (
          <p className="muted doc-empty">
            Complete the Architecture step to see cloud cost estimates here.
          </p>
        )}
      </div>
    </section>
  );
}
