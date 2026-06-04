import { DESCRIPTION_MAX_TOKENS } from "../constants/wizard.js";

export function estimateTokenCount(text) {
  const stripped = text.trim();
  if (!stripped) return 0;
  return Math.max(1, Math.ceil(stripped.length / 4));
}

export function validateProjectForm(form) {
  const errors = {};
  if (!form.name.trim()) errors.name = "Project name is required.";
  if (!form.description.trim()) {
    errors.description = "Project description is required.";
  } else if (estimateTokenCount(form.description) > DESCRIPTION_MAX_TOKENS) {
    errors.description = `Project description must be ${DESCRIPTION_MAX_TOKENS} tokens or fewer.`;
  }
  if (form.project_types.length === 0) {
    errors.project_types = "Select at least one project type.";
  }
  return errors;
}

export function buildInputKey(form, answers) {
  return JSON.stringify({ form, answers });
}
