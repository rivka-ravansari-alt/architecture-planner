import { WIZARD_STEPS, STEP_SUBTITLES } from "../../constants/wizard.js";

export default function Topbar({ step, user, loading, onReset, onLogout, showReset }) {
  return (
    <header className="topbar">
      <div className="topbar-text">
        <h1>{WIZARD_STEPS[step - 1]}</h1>
        <p>{STEP_SUBTITLES[step - 1]}</p>
      </div>
      <div className="topbar-actions">
        {showReset && (
          <button
            type="button"
            className="btn btn-ghost btn-reset"
            onClick={onReset}
            disabled={loading}
            title="Clear all answers and start a new plan"
          >
            Reset Project
          </button>
        )}
        <div className="user-menu">
          {user.picture && (
            <img className="user-avatar" src={user.picture} alt="" width={32} height={32} />
          )}
          <span className="user-name">{user.name || user.email}</span>
          <button type="button" className="btn btn-ghost" onClick={onLogout} disabled={loading}>
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}
