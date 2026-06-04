import { useAuth } from "../context/AuthContext.jsx";

export default function LoginPage() {
  const { login } = useAuth();

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Archsari</h1>
        <p>Sign in to plan your application architecture with AI.</p>
        <button type="button" className="btn btn-primary btn-google" onClick={login}>
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
