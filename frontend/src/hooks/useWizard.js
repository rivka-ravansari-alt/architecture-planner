import { useCallback, useEffect, useState } from "react";

import {
  SAMPLE_COMPONENTS,
  SAMPLE_COSTS,
  SAMPLE_PROJECT,
} from "../constants/sampleArchitecture.js";
import { EMPTY_INTAKE_FORM } from "../utils/intakeFormState.js";

/**
 * Static wizard state. All backend/AI functionality has been removed — the
 * wizard only navigates between screens locally and renders the hardcoded
 * sample architecture. No generation, validation, persistence, or cost
 * computation happens here.
 */
export function useWizard() {
  const [step, setStep] = useState(1);
  const [intakeForm, setIntakeForm] = useState(EMPTY_INTAKE_FORM);
  const [components, setComponents] = useState(() =>
    SAMPLE_COMPONENTS.map((component) => ({ ...component }))
  );
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const maxStep = 3;
  const project = SAMPLE_PROJECT;
  const derived = { costs: SAMPLE_COSTS };
  const inWorkspace = step === 3;

  useEffect(() => {
    setSidebarCollapsed(inWorkspace);
  }, [inWorkspace]);

  const goToStep = useCallback((target) => {
    if (target < 1 || target > maxStep) return;
    setStep(target);
  }, []);

  const goNext = useCallback(() => {
    setStep((current) => Math.min(current + 1, maxStep));
  }, []);

  const goBack = useCallback(() => {
    setStep((current) => Math.max(current - 1, 1));
  }, []);

  const reset = useCallback(() => {
    setIntakeForm(EMPTY_INTAKE_FORM);
    setComponents(SAMPLE_COMPONENTS.map((component) => ({ ...component })));
    setStep(1);
  }, []);

  const moveComponent = useCallback((index, optional) => {
    setComponents((previous) =>
      previous.map((component, componentIndex) =>
        componentIndex === index ? { ...component, optional } : component
      )
    );
  }, []);

  const primaryLabel = step === 2 ? "View Architecture" : "Continue";

  return {
    step,
    maxStep,
    intakeForm,
    setIntakeForm,
    errors: {},
    project,
    components,
    loading: false,
    error: null,
    derived,
    needsGeneration: false,
    inWorkspace,
    sidebarCollapsed,
    setSidebarCollapsed,
    goToStep,
    goNext,
    goBack,
    reset,
    moveComponent,
    primaryLabel,
    showStaleNotice: false,
  };
}
