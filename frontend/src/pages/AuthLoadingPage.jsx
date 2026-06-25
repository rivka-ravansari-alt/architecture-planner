import { Spinner } from "../components/ui/Spinner.jsx";

export default function AuthLoadingPage({ message = "Checking your session…" }) {
  return (
    <div className="login-page">
      <div className="login-card">
        <Spinner />
        <p>{message}</p>
      </div>
    </div>
  );
}
