import { Spinner } from "../components/ui/Spinner.jsx";

export default function AuthLoadingPage() {
  return (
    <div className="login-page">
      <div className="login-card">
        <Spinner />
        <p>Loading…</p>
      </div>
    </div>
  );
}
