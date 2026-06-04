import { STAGES, EXPECTED_USERS, DESCRIPTION_MAX_TOKENS } from "../../constants/wizard.js";
import { estimateTokenCount } from "../../utils/validation.js";

export default function StepProjectDetails({ form, setForm, projectTypes, errors }) {
  const toggleType = (id) => {
    setForm((previous) => {
      const exists = previous.project_types.includes(id);
      return {
        ...previous,
        project_types: exists
          ? previous.project_types.filter((type) => type !== id)
          : [...previous.project_types, id],
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
          onChange={(event) => setForm({ ...form, name: event.target.value })}
        />
        {errors.name && <div className="error-text">{errors.name}</div>}
      </div>

      <div className="field">
        <label htmlFor="description">Project description</label>
        <textarea
          id="description"
          placeholder="A short description of what the app does..."
          value={form.description}
          onChange={(event) => setForm({ ...form, description: event.target.value })}
        />
        <div className={`field-hint ${descriptionOverLimit ? "error-text" : ""}`}>
          {descriptionTokens} / {DESCRIPTION_MAX_TOKENS} tokens
        </div>
        {errors.description && <div className="error-text">{errors.description}</div>}
      </div>

      <div className="field">
        <label>Project type (select one or more)</label>
        <div className="chips">
          {projectTypes.map((type) => (
            <div
              key={type.id}
              className={`chip ${form.project_types.includes(type.id) ? "selected" : ""}`}
              onClick={() => toggleType(type.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(event) =>
                (event.key === "Enter" || event.key === " ") && toggleType(type.id)
              }
            >
              {type.label}
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
            onChange={(event) => setForm({ ...form, stage: event.target.value })}
          >
            {STAGES.map((stage) => (
              <option key={stage.id} value={stage.id}>
                {stage.label}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="users">Expected users</label>
          <select
            id="users"
            value={form.expected_users}
            onChange={(event) => setForm({ ...form, expected_users: event.target.value })}
          >
            {EXPECTED_USERS.map((users) => (
              <option key={users.id} value={users.id}>
                {users.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
