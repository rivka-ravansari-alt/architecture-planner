import UsageForm from "../intake/UsageForm.jsx";

export default function StepRequirements({ intakeForm, setIntakeForm, errors }) {
  return (
    <UsageForm
      value={intakeForm}
      onChange={setIntakeForm}
      errors={errors}
      showHeader={false}
    />
  );
}
