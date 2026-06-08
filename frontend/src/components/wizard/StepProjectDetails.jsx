import DynamicForm from "../intake/DynamicForm.jsx";

export default function StepProjectDetails({ intakeForm, setIntakeForm, errors }) {
  return (
    <DynamicForm
      section="basic"
      value={intakeForm}
      onChange={setIntakeForm}
      errors={errors}
    />
  );
}
