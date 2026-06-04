import { STEPS, SIDEBAR_STEP_ICON_PATHS } from "../../constants/navigation.js";

function NavIcon({ children }) {
  return (
    <svg
      className="nav-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {children}
    </svg>
  );
}

export default function Sidebar({
  current,
  maxStep,
  onStepClick,
  loading,
  collapsed = false,
  focusMode = false,
  onToggleCollapse,
}) {
  return (
    <aside
      className={`sidebar ${collapsed ? "is-collapsed" : ""} ${focusMode ? "in-focus-mode" : ""}`}
      aria-label="Application navigation"
    >
      <div className="brand">
        <div className="brand-mark">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 21h18 M5 21V7l8-4v18 M19 21V11l-6-3" />
          </svg>
        </div>
        <div className="brand-text">
          <span className="brand-name">Archsari</span>
          <span className="brand-sub">Architecture Before Code</span>
        </div>
      </div>

      {focusMode && (
        <button
          type="button"
          className="sidebar-focus-toggle"
          onClick={onToggleCollapse}
          aria-expanded={!collapsed}
          title={collapsed ? "Expand application menu" : "Collapse application menu"}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            {collapsed ? (
              <path d="M9 18l6-6-6-6 M15 6h4 M15 12h4 M15 18h4" />
            ) : (
              <path d="M15 18l-6-6 6-6 M9 6H5 M9 12H5 M9 18H5" />
            )}
          </svg>
          <span className="sidebar-focus-toggle-label">
            {collapsed ? "Expand menu" : "Collapse menu"}
          </span>
        </button>
      )}

      <nav className="side-nav">
        <span className="side-nav-label">Planning</span>
        {STEPS.map((label, index) => {
          const stepNum = index + 1;
          const locked = stepNum > maxStep;
          const state = locked
            ? "locked"
            : stepNum === current
              ? "active"
              : stepNum < current
                ? "done"
                : "";

          return (
            <button
              type="button"
              key={label}
              className={`nav-item ${state}`}
              onClick={() => onStepClick(stepNum)}
              disabled={loading || locked || stepNum === current}
              aria-current={stepNum === current ? "step" : undefined}
              aria-disabled={locked || undefined}
              title={label}
            >
              <NavIcon>
                <path d={SIDEBAR_STEP_ICON_PATHS[index]} />
              </NavIcon>
              <span className="nav-item-label">{label}</span>
              <span className="nav-step">
                {stepNum < current ? (
                  <svg
                    className="check"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                ) : (
                  stepNum
                )}
              </span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">Architecture Before Code</div>
    </aside>
  );
}
