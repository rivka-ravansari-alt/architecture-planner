import Sidebar from "./Sidebar.jsx";
import Topbar from "./Topbar.jsx";
import ErrorBanner from "../ui/ErrorBanner.jsx";
import StaleNotice from "../wizard/StaleNotice.jsx";
import WizardActions from "../wizard/WizardActions.jsx";
import StepProjectDetails from "../wizard/StepProjectDetails.jsx";
import StepRequirements from "../wizard/StepRequirements.jsx";
import StepComponentReview from "../wizard/StepComponentReview.jsx";
import ArchitectureWorkspace from "../../features/architecture/components/ArchitectureWorkspace.jsx";

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
    canGeneratePricing,
    inWorkspace,
    sidebarCollapsed,
    setSidebarCollapsed,
    goToStep,
    goNext,
    goBack,
    reset,
    moveComponent,
    removeComponent,
    addComponent,
    updateComponent,
    primaryLabel,
    showStaleNotice,
    approveComponentsAndGenerateDiagrams,
    generatePricing,
  } = wizard;

  return (
    <div className={`app-shell ${inWorkspace ? "focus-mode" : ""}`}>
      <Sidebar
        current={step}
        maxStep={maxStep}
        onStepClick={goToStep}
        loading={loading}
        collapsed={inWorkspace && sidebarCollapsed}
        focusMode={inWorkspace}
        onToggleCollapse={() => setSidebarCollapsed((collapsed) => !collapsed)}
      />

      <main className="main">
        {!inWorkspace && (
          <Topbar
            step={step}
            user={user}
            loading={loading}
            onReset={reset}
            onLogout={onLogout}
            showReset={project !== null || step > 1}
          />
        )}

        <div className={`content ${inWorkspace ? "content-workspace content-focus" : ""}`}>
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
            <StepRequirements intakeForm={intakeForm} setIntakeForm={setIntakeForm} />
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
              onGenerateArchitecture={approveComponentsAndGenerateDiagrams}
            />
          )}

          {inWorkspace && (
            <ArchitectureWorkspace
              project={project}
              projectTypes={projectTypes}
              components={components}
              costs={derived?.costs}
              hasPricing={hasPricing}
              canGeneratePricing={canGeneratePricing}
              loading={loading}
              onGeneratePricing={generatePricing}
              onExit={() => goToStep(3)}
              onReset={reset}
              onToggleAppSidebar={() => setSidebarCollapsed((collapsed) => !collapsed)}
              appSidebarCollapsed={sidebarCollapsed}
            />
          )}

          {step < 3 && (
            <WizardActions
              step={step}
              loading={loading}
              primaryLabel={primaryLabel}
              onBack={goBack}
              onNext={goNext}
            />
          )}
        </div>
      </main>
    </div>
  );
}
