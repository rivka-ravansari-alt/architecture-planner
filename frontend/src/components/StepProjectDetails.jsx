import { STAGES, EXPECTED_USERS, DESCRIPTION_MAX_TOKENS, estimateTokenCount } from "../constants.js";

export default function StepProjectDetails({ form, setForm, projectTypes, errors }) {
  const toggleType = (id) => {
    setForm((prev) => {
      const exists = prev.project_types.includes(id);
      return {
        ...prev,
        project_types: exists
          ? prev.project_types.filter((t) => t !== id)
          : [...prev.project_types, id],
      };
    });
  };

  const descriptionTokens = estimateTokenCount(form.description);
  const descriptionOverLimit = descriptionTokens > DESCRIPTION_MAX_TOKENS;

  return (
    <div className="card">
      <div className="field">
        <label htmlFor="name">Project name</label>
        <input
          id="name"
          type="text"
          placeholder="e.g. Task Manager"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
        {errors.name && <div className="error-text">{errors.name}</div>}
      </div>

      <div className="field">
        <label htmlFor="description">Project description</label>
        <textarea
          id="description"
          placeholder="A short description of what the app does..."
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
        <div className={`field-hint ${descriptionOverLimit ? "error-text" : ""}`}>
          {descriptionTokens} / {DESCRIPTION_MAX_TOKENS} tokens
        </div>
        {errors.description && <div className="error-text">{errors.description}</div>}
      </div>

      <div className="field">
        <label>Project type (select one or more)</label>
        <div className="chips">
          {projectTypes.map((t) => (
            <div
              key={t.id}
              className={`chip ${form.project_types.includes(t.id) ? "selected" : ""}`}
              onClick={() => toggleType(t.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && toggleType(t.id)}
            >
              {t.label}
            </div>
          ))}
        </div>
        {errors.project_types && <div className="error-text">{errors.project_types}</div>}
      </div>

      <div className="grid-2">
        <div className="field">
          <label htmlFor="stage">Stage</label>
          <select
            id="stage"
            value={form.stage}
            onChange={(e) => setForm({ ...form, stage: e.target.value })}
          >
            {STAGES.map((s) => (
              <option key={s.id} value={s.id}>{s.label}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="users">Expected users</label>
          <select
            id="users"
            value={form.expected_users}
            onChange={(e) => setForm({ ...form, expected_users: e.target.value })}
          >
            {EXPECTED_USERS.map((u) => (
              <option key={u.id} value={u.id}>{u.label}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
