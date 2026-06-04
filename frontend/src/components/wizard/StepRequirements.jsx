import { REQUIREMENTS } from "../../constants/wizard.js";

export default function StepRequirements({ answers, setAnswers }) {
  const toggle = (key) => setAnswers({ ...answers, [key]: !answers[key] });

  return (
    <div className="card">
      {REQUIREMENTS.map((requirement) => (
        <div className="toggle-row" key={requirement.key}>
          <span className="label">{requirement.label}</span>
          <label className="switch">
            <input
              type="checkbox"
              checked={!!answers[requirement.key]}
              onChange={() => toggle(requirement.key)}
            />
            <span className="slider" />
          </label>
        </div>
      ))}
    </div>
  );
}
