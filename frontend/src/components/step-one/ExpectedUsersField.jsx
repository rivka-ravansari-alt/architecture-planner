/**
 * Expected number of users input (whole numbers > 0, with thousands separators).
 * @param {{ value: string, onChange: (digits: string) => void, error?: string }} props
 */
export default function ExpectedUsersField({ value, onChange, error }) {
  const displayValue =
    value && Number(value) > 0 ? Number(value).toLocaleString() : value;

  const handleChange = (event) => {
    const digits = event.target.value.replace(/\D/g, "");
    onChange(digits);
  };

  return (
    <div className="field">
      <label htmlFor="expected-users">Expected number of users</label>
      <input
        id="expected-users"
        type="text"
        inputMode="numeric"
        autoComplete="off"
        className="input-compact"
        placeholder="e.g. 5000"
        value={displayValue}
        onChange={handleChange}
      />
      {error && <p className="error-text">{error}</p>}
    </div>
  );
}
