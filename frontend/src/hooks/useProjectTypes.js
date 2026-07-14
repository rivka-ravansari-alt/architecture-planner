import { SAMPLE_PROJECT_TYPES } from "../constants/sampleArchitecture.js";

/** Static project types — the backend fetch has been removed. */
export function useProjectTypes() {
  return { projectTypes: SAMPLE_PROJECT_TYPES, error: null };
}
