import { useState } from "react";

import { useAuth } from "./context/AuthContext.jsx";
import StepOneForm from "./components/step-one/StepOneForm.jsx";
import ComponentSelectionScreen from "./components/step-two/ComponentSelectionScreen.jsx";
import PricingScreen from "./components/step-four/PricingScreen.jsx";
import AuthLoadingPage from "./pages/AuthLoadingPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";

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
        <span className="step-one-brand">Archsari</span>
        <div className="step-one-user">
          {user.name && <span>{user.name}</span>}
          <button type="button" className="btn btn-ghost" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>
      <main className="step-one-main">
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
      </main>
    </div>
  );
}
