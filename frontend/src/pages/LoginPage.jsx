import { useAuth } from "../context/AuthContext.jsx";

export default function LoginPage() {
  const { login } = useAuth();

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <h1>ArchSari</h1>
          <p className="brand-tagline">Know Your Cloud Costs Before You Start</p>
        </div>
        <p className="login-subtitle">Sign in to plan your application architecture with AI.</p>
        <button type="button" className="btn btn-primary btn-google" onClick={login}>
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
