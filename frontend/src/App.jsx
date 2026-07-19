import { lazy, Suspense, useState } from "react";

import { useAuth } from "./context/AuthContext.jsx";
import { Spinner } from "./components/ui/Spinner.jsx";
import AuthLoadingPage from "./pages/AuthLoadingPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";

const StepOneForm = lazy(() => import("./components/step-one/StepOneForm.jsx"));
const ComponentSelectionScreen = lazy(() =>
  import("./components/step-two/ComponentSelectionScreen.jsx")
);
const PricingScreen = lazy(() =>
  import("./components/step-four/PricingScreen.jsx")
);

export default function App() {
  const { user, loading, logout } = useAuth();
  const [projectId, setProjectId] = useState(null);
  const [step, setStep] = useState("components");

  if (loading) {
    return <AuthLoadingPage />;
  }

  if (!user) {
    return <LoginPage />;
  }

  const handleProjectCreated = (id) => {
    setProjectId(id);
    setStep("components");
  };

  const handleBackToIntake = () => {
    setProjectId(null);
    setStep("components");
  };

  return (
    <div className="step-one-page">
      <header className="step-one-topbar">
        <div className="step-one-brand">
          <span className="step-one-brand-name">ArchSari</span>
          <span className="brand-tagline">Know Your Cloud Costs Before You Start</span>
        </div>
        <div className="step-one-user">
          {user.name && <span>{user.name}</span>}
          <button type="button" className="btn btn-ghost" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>
      <main className="step-one-main">
        <Suspense fallback={<Spinner className="spinner-lg" />}>
          {!projectId ? (
            <StepOneForm onCreated={handleProjectCreated} />
          ) : step === "pricing" ? (
            <PricingScreen
              projectId={projectId}
              onBack={() => setStep("components")}
            />
          ) : (
            <ComponentSelectionScreen
              projectId={projectId}
              onBack={handleBackToIntake}
              onContinue={() => setStep("pricing")}
            />
          )}
        </Suspense>
      </main>
    </div>
  );
}
