/**
 * Application description input.
 * @param {{ value: string, onChange: (value: string) => void, error?: string }} props
 */
export default function AppDescriptionField({ value, onChange, error }) {
  return (
    <div className="field">
      <label htmlFor="app-description">Application description</label>
      <textarea
        id="app-description"
        rows={5}
        placeholder="Describe what you are building, who it is for, and the core problem it solves."
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
      {error && <p className="error-text">{error}</p>}
    </div>
  );
}
