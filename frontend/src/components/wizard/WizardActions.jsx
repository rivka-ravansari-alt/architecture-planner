import { Spinner } from "../ui/Spinner.jsx";

export default function WizardActions({ step, loading, primaryLabel, onBack, onNext }) {
  return (
    <div className="actions">
      {step > 1 ? (
        <button type="button" className="btn btn-ghost" onClick={onBack} disabled={loading}>
          Back
        </button>
      ) : (
        <span />
      )}

      {step < 3 && (
        <button type="button" className="btn btn-primary" onClick={onNext} disabled={loading}>
          {loading && <Spinner />}
          {primaryLabel}
        </button>
      )}
    </div>
  );
}
