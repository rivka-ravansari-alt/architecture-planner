import { Spinner } from "../ui/Spinner.jsx";

export default function WizardActions({
  step,
  loading,
  primaryLabel,
  primaryDisabled = false,
  showPrimary = true,
  secondaryLabel,
  secondaryDisabled = false,
  showSecondary = false,
  onBack,
  onNext,
  onSecondary,
}) {
  return (
    <div className="actions">
      {step > 1 ? (
        <button type="button" className="btn btn-ghost" onClick={onBack} disabled={loading}>
          Back
        </button>
      ) : (
        <span />
      )}

      <div className="actions-primary-group">
        {showSecondary && (
          <button
            type="button"
            className="btn btn-ghost"
            onClick={onSecondary}
            disabled={loading || secondaryDisabled}
          >
            {secondaryLabel}
          </button>
        )}

        {showPrimary && (
          <button
            type="button"
            className="btn btn-primary"
            onClick={onNext}
            disabled={loading || primaryDisabled}
          >
            {loading && <Spinner />}
            {primaryLabel}
          </button>
        )}
      </div>
    </div>
  );
}
