import { useState } from "react";

import { projectApi } from "../../api/projectApi.js";
import { Spinner } from "../ui/Spinner.jsx";
import AppDescriptionField from "./AppDescriptionField.jsx";
import ExpectedUsersField from "./ExpectedUsersField.jsx";
import RequirementsForm from "./RequirementsForm.jsx";
import StageSelector from "./StageSelector.jsx";
import {
  buildInitialRequirements,
  serializeRequirements,
  validateRequirements,
} from "./requirementsConfig.js";

export default function StepOneForm({ onCreated }) {
  const [description, setDescription] = useState("");
  const [stage, setStage] = useState("mvp");
  const [expectedUsers, setExpectedUsers] = useState("");
  const [requirements, setRequirements] = useState(buildInitialRequirements);

  const [fieldError, setFieldError] = useState("");
  const [usersError, setUsersError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitError("");

    if (!description.trim()) {
      setFieldError("Please describe your application.");
      return;
    }
    setFieldError("");

    const usersValue = Number(expectedUsers);
    if (
      expectedUsers === "" ||
      !Number.isInteger(usersValue) ||
      usersValue <= 0
    ) {
      setUsersError("Enter a whole number greater than 0.");
      return;
    }
    setUsersError("");

    const requirementErrors = validateRequirements(requirements);
    if (Object.keys(requirementErrors).length > 0) {
      setSubmitError("Please fix the highlighted requirement fields.");
      return;
    }

    setLoading(true);
    try {
      const result = await projectApi.createProject({
        description: description.trim(),
        stage,
        expected_users: usersValue,
        requirements: serializeRequirements(requirements),
      });
      onCreated?.(result.id);
    } catch (error) {
      setSubmitError(error.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="dynamic-form" onSubmit={handleSubmit}>
      <div className="card">
        <h2>Create a project</h2>
        <p className="subtitle">
          Tell us about your application. We will use this in the next steps.
        </p>

        <AppDescriptionField
          value={description}
          onChange={setDescription}
          error={fieldError}
        />
        <StageSelector value={stage} onChange={setStage} />
        <ExpectedUsersField
          value={expectedUsers}
          onChange={(next) => {
            setExpectedUsers(next);
            if (usersError) setUsersError("");
          }}
          error={usersError}
        />
      </div>

      <div className="card">
        <h2>Requirements</h2>
        <p className="subtitle">
          Enable what your application needs. Add a few details where relevant -
          you only need to answer what you already know.
        </p>
        <RequirementsForm value={requirements} onChange={setRequirements} />
      </div>

      {submitError && <p className="error-text">{submitError}</p>}

      <div className="actions">
        <span />
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading && <Spinner />}
          Continue to components
        </button>
      </div>
    </form>
  );
}
