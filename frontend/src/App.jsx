import { useAuth } from "./context/AuthContext.jsx";
import AppShell from "./components/layout/AppShell.jsx";
import { useProjectTypes } from "./hooks/useProjectTypes.js";
import { useComponentCatalog } from "./hooks/useComponentCatalog.js";
import { useWizard } from "./hooks/useWizard.js";
import AuthLoadingPage from "./pages/AuthLoadingPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import ErrorBanner from "./components/ui/ErrorBanner.jsx";

function AuthenticatedApp({ user, onLogout }) {
  const wizard = useWizard();
  const { projectTypes, error: projectTypesError } = useProjectTypes();
  const { componentCatalog, error: componentCatalogError } = useComponentCatalog();

  return (
    <>
      <ErrorBanner message={projectTypesError || componentCatalogError} />
      <AppShell
        user={user}
        wizard={wizard}
        projectTypes={projectTypes}
        componentCatalog={componentCatalog}
        onLogout={onLogout}
      />
    </>
  );
}

export default function App() {
  const { user, loading: authLoading, loadingMessage, logout } = useAuth();

  if (authLoading) {
    return <AuthLoadingPage message={loadingMessage} />;
  }

  if (!user) {
    return <LoginPage />;
  }

  return <AuthenticatedApp user={user} onLogout={logout} />;
}
