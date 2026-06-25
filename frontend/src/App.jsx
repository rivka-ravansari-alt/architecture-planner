import { useAuth } from "./context/AuthContext.jsx";
import AppShell from "./components/layout/AppShell.jsx";
import { useProjectTypes } from "./hooks/useProjectTypes.js";
import { useComponentCatalog } from "./hooks/useComponentCatalog.js";
import { useWizard } from "./hooks/useWizard.js";
import AuthLoadingPage from "./pages/AuthLoadingPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import ErrorBanner from "./components/ui/ErrorBanner.jsx";

export default function App() {
  const { user, loading: authLoading, logout } = useAuth();
  const wizard = useWizard();
  const { projectTypes, error: projectTypesError } = useProjectTypes();
  const { componentCatalog, error: componentCatalogError } = useComponentCatalog();

  if (authLoading) {
    return <AuthLoadingPage />;
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <>
      <ErrorBanner message={projectTypesError || componentCatalogError} />
      <AppShell
        user={user}
        wizard={wizard}
        projectTypes={projectTypes}
        componentCatalog={componentCatalog}
        onLogout={logout}
      />
    </>
  );
}
