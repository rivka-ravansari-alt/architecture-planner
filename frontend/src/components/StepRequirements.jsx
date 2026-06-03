import { REQUIREMENTS } from "../constants.js";

export default function StepRequirements({ answers, setAnswers }) {
  const toggle = (key) => setAnswers({ ...answers, [key]: !answers[key] });

  return (
    <div className="card">
      {REQUIREMENTS.map((r) => (
        <div className="toggle-row" key={r.key}>
          <span className="label">{r.label}</span>
          <label className="switch">
            <input
              type="checkbox"
              checked={!!answers[r.key]}
              onChange={() => toggle(r.key)}
            />
            <span className="slider" />
          </label>
        </div>
      ))}
    </div>
  );
}
