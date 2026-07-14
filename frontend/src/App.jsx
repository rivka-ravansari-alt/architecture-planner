import { useState } from "react";

import { useAuth } from "./context/AuthContext.jsx";
import StepOneForm from "./components/step-one/StepOneForm.jsx";
import ComponentSelectionScreen from "./components/step-two/ComponentSelectionScreen.jsx";
import AuthLoadingPage from "./pages/AuthLoadingPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";

export default function App() {
  const { user, loading, logout } = useAuth();
  const [projectId, setProjectId] = useState(null);

  if (loading) {
    return <AuthLoadingPage />;
  }

  if (!user) {
    return <LoginPage />;
  }

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
        {projectId ? (
          <ComponentSelectionScreen
            projectId={projectId}
            onBack={() => setProjectId(null)}
          />
        ) : (
          <StepOneForm onCreated={setProjectId} />
        )}
      </main>
    </div>
  );
}
