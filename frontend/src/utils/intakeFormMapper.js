import { LEGACY_ANSWER_MAPPING } from "../config/intakeFormConfig.js";
import { buildIntakeOutput } from "./intakeFormState.js";

const PLATFORM_TO_PROJECT_TYPE = {
  web: "web_app",
  mobile: "mobile_app",
};

/**
 * Maps the intake form JSON to the legacy API payload expected by the backend.
 * @param {ReturnType<import("./intakeFormState.js").createEmptyIntakeForm>} intakeForm
 */
export function toLegacyPayload(intakeForm) {
  const output = buildIntakeOutput(intakeForm);
  const { product, features } = output;

  /** @type {string[]} */
  const projectTypes = [];
  for (const platform of product.platforms) {
    const mapped = PLATFORM_TO_PROJECT_TYPE[platform];
    if (mapped && !projectTypes.includes(mapped)) {
      projectTypes.push(mapped);
    }
  }

  if (projectTypes.length === 0 && product.platforms.includes("both")) {
    projectTypes.push("web_app", "mobile_app");
  }

  /** @type {Record<string, boolean>} */
  const answers = {};
  for (const [key, resolver] of Object.entries(LEGACY_ANSWER_MAPPING)) {
    answers[key] = resolver(features);
  }

  return {
    name: product.name,
    description: product.description,
    project_types: projectTypes,
    stage: product.stage || "mvp",
    expected_users: product.expected_users || "100",
    answers,
  };
}
