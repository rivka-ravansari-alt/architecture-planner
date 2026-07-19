import { Spinner } from "../components/ui/Spinner.jsx";

export default function AuthLoadingPage() {
  return (
    <div className="login-page">
      <div className="login-card login-loading">
        <Spinner className="spinner-lg" />
        <p className="login-subtitle">Loading…</p>
      </div>
    </div>
  );
}
