import StepArchitecture from "../wizard/StepArchitecture.jsx";
import StepComponentReview from "../wizard/StepComponentReview.jsx";
import StepPricing from "../wizard/StepPricing.jsx";
import StepProjectDetails from "../wizard/StepProjectDetails.jsx";
import StepRequirements from "../wizard/StepRequirements.jsx";
import StepSummary from "../wizard/StepSummary.jsx";
import StaleNotice from "../wizard/StaleNotice.jsx";
import WizardActions from "../wizard/WizardActions.jsx";
import ErrorBanner from "../ui/ErrorBanner.jsx";
import Sidebar from "./Sidebar.jsx";
import Topbar from "./Topbar.jsx";

export default function AppShell({
  user,
  wizard,
  projectTypes,
  componentCatalog,
  onLogout,
}) {
  const {
    step,
    maxStep,
    intakeForm,
    setIntakeForm,
    errors,
    project,
    components,
    loading,
    error,
    derived,
    hasPricing,
    goToStep,
    goNext,
    goBack,
    reset,
    moveComponent,
    removeComponent,
    addComponent,
    updateComponent,
    primaryLabel,
    primaryDisabled,
    showPrimaryAction,
    showStaleNotice,
    showSkipArchitecture,
    canSkipArchitecture,
    skipArchitecture,
  } = wizard;

  const isWideStep = step >= 4;

  return (
    <div className="app-shell">
      <Sidebar
        current={step}
        maxStep={maxStep}
        onStepClick={goToStep}
        loading={loading}
      />

      <main className="main">
        <Topbar
          step={step}
          user={user}
          loading={loading}
          onReset={reset}
          onLogout={onLogout}
          showReset={project !== null || step > 1}
        />

        <div className={`content ${isWideStep ? "content-wide" : ""}`}>
          <ErrorBanner message={error} />
          {showStaleNotice && <StaleNotice />}

          {step === 1 && (
            <StepProjectDetails
              intakeForm={intakeForm}
              setIntakeForm={setIntakeForm}
              errors={errors}
            />
          )}

          {step === 2 && (
            <StepRequirements
              intakeForm={intakeForm}
              setIntakeForm={setIntakeForm}
              errors={errors}
            />
          )}

          {step === 3 && (
            <StepComponentReview
              components={components}
              componentCatalog={componentCatalog}
              loading={loading}
              onMove={moveComponent}
              onRemove={removeComponent}
              onAdd={addComponent}
              onUpdate={updateComponent}
            />
          )}

          {step === 4 && project && (
            <StepArchitecture project={project} components={components} />
          )}

          {step === 5 && (
            <StepPricing components={components} costs={derived?.costs} />
          )}

          {step === 6 && project && (
            <StepSummary
              intakeForm={intakeForm}
              project={project}
              projectTypes={projectTypes}
              components={components}
              costs={derived?.costs}
            />
          )}

          <WizardActions
            step={step}
            loading={loading}
            primaryLabel={primaryLabel}
            primaryDisabled={primaryDisabled}
            showPrimary={showPrimaryAction}
            showSecondary={showSkipArchitecture}
            secondaryLabel="Skip Architecture"
            secondaryDisabled={!canSkipArchitecture}
            onBack={goBack}
            onNext={goNext}
            onSecondary={skipArchitecture}
          />
        </div>
      </main>
    </div>
  );
}
