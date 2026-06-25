import DynamicForm from "../intake/DynamicForm.jsx";

export default function StepRequirements({ intakeForm, setIntakeForm }) {
  return <DynamicForm section="features" value={intakeForm} onChange={setIntakeForm} showHeader={false} />;
}
