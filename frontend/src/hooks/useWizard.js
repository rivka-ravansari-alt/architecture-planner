import { useCallback, useEffect, useMemo, useState } from "react";

import { api } from "../api/index.js";
import { deriveArchitecture } from "../features/architecture/utils/deriveArchitecture.js";
import { WORKFLOW_STATUS } from "../constants/wizard.js";
import { componentsToApiPayload } from "../utils/componentPayload.js";
import { buildIntakeOutput, EMPTY_INTAKE_FORM } from "../utils/intakeFormState.js";
import { toLegacyPayload } from "../utils/intakeFormMapper.js";
import { buildInputKey, validateBasicProduct } from "../utils/validation.js";

function cloneComponents(components) {
  return components.map((component) => ({ ...component }));
}

export function useWizard() {
  const [step, setStep] = useState(1);
  const [maxStep, setMaxStep] = useState(1);
  const [intakeForm, setIntakeForm] = useState(EMPTY_INTAKE_FORM);
  const [errors, setErrors] = useState({});
  const [project, setProject] = useState(null);
  const [components, setComponents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [savedKey, setSavedKey] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const inputKey = useMemo(() => buildInputKey(intakeForm), [intakeForm]);
  const needsSave = project === null || savedKey !== inputKey;
  const inWorkspace = step === 4 && project;
  const hasPricing =
    project?.workflow_status === WORKFLOW_STATUS.PRICING_GENERATED ||
    (project?.cost_estimates?.length ?? 0) > 0;
  const canGeneratePricing =
    project?.workflow_status === WORKFLOW_STATUS.DIAGRAMS_GENERATED ||
    project?.workflow_status === WORKFLOW_STATUS.ARCHITECTURE_APPROVED ||
    project?.workflow_status === WORKFLOW_STATUS.PRICING_GENERATED;

  const derived = useMemo(
    () => (project ? deriveArchitecture(project, components) : null),
    [project, components]
  );

  useEffect(() => {
    setSidebarCollapsed(Boolean(inWorkspace));
  }, [inWorkspace]);

  const validateStep1 = useCallback(() => {
    const nextErrors = validateBasicProduct(intakeForm);
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }, [intakeForm]);

  const getIntakeOutput = useCallback(() => buildIntakeOutput(intakeForm), [intakeForm]);

  const unlockAndGo = useCallback((target) => {
    setMaxStep((current) => Math.max(current, target));
    setStep(target);
  }, []);

  const syncProject = useCallback((nextProject) => {
    setProject(nextProject);
    setComponents(cloneComponents(nextProject.components));
  }, []);

  const saveProject = useCallback(async () => {
    const payload = toLegacyPayload(intakeForm);
    const created = await api.createProject(payload);
    syncProject(created);
    setSavedKey(inputKey);
    return created;
  }, [intakeForm, inputKey, syncProject]);

  const generateComponents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let current = project;
      if (needsSave || !current) {
        current = await saveProject();
      }
      const generated = await api.generateComponents(current.id);
      syncProject(generated);
      unlockAndGo(3);
      setStep(3);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [project, needsSave, saveProject, syncProject, unlockAndGo]);

  const approveComponentsAndGenerateDiagrams = useCallback(async () => {
    if (!project || components.length === 0) {
      setError("Add at least one component before generating architecture.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const payload = componentsToApiPayload(components);
      const approved = await api.updateComponents(project.id, payload);
      syncProject(approved);
      const withDiagrams = await api.generateDiagrams(approved.id);
      syncProject(withDiagrams);
      unlockAndGo(4);
      setStep(4);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [project, components, syncProject, unlockAndGo]);

  const generatePricing = useCallback(async () => {
    if (!project || !canGeneratePricing) return;

    setLoading(true);
    setError(null);
    try {
      let current = project;
      if (
        current.workflow_status === WORKFLOW_STATUS.DIAGRAMS_GENERATED ||
        current.workflow_status === WORKFLOW_STATUS.PRICING_GENERATED
      ) {
        current = await api.approveArchitecture(project.id);
        syncProject(current);
      }
      const withPricing = await api.generatePricing(current.id);
      syncProject(withPricing);
      return withPricing;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [project, canGeneratePricing, syncProject]);

  const goToStep = useCallback(
    async (target) => {
      setError(null);
      if (target === step || loading) return;
      if (target < 1 || target > maxStep) return;

      if (target >= 3 && !validateStep1()) {
        setStep(1);
        return;
      }

      setStep(target);
    },
    [step, loading, maxStep, validateStep1]
  );

  const goNext = useCallback(async () => {
    setError(null);
    if (loading) return;

    if (step === 1) {
      if (!validateStep1()) return;
      unlockAndGo(2);
      return;
    }

    if (step === 2) {
      if (!validateStep1()) {
        setStep(1);
        return;
      }
      await generateComponents();
    }
  }, [step, loading, validateStep1, unlockAndGo, generateComponents]);

  const goBack = useCallback(() => {
    if (step > 1) goToStep(step - 1);
  }, [step, goToStep]);

  const reset = useCallback(() => {
    setIntakeForm(EMPTY_INTAKE_FORM);
    setProject(null);
    setComponents([]);
    setSavedKey(null);
    setErrors({});
    setError(null);
    setMaxStep(1);
    setStep(1);
  }, []);

  const persistComponents = useCallback(
    async (updater) => {
      let nextComponents;
      setComponents((previous) => {
        nextComponents =
          typeof updater === "function" ? updater(previous) : updater;
        return nextComponents;
      });

      if (!project || !nextComponents) return;

      try {
        const approved = await api.updateComponents(
          project.id,
          componentsToApiPayload(nextComponents)
        );
        syncProject(approved);
      } catch (err) {
        setError(err.message);
      }
    },
    [project, syncProject]
  );

  const moveComponent = useCallback(
    (index, optional) => {
      persistComponents((previous) =>
        previous.map((component, componentIndex) =>
          componentIndex === index ? { ...component, optional } : component
        )
      );
    },
    [persistComponents]
  );

  const removeComponent = useCallback(
    (index) => {
      persistComponents((previous) =>
        previous.filter((_, componentIndex) => componentIndex !== index)
      );
    },
    [persistComponents]
  );

  const addComponent = useCallback((component) => {
    setComponents((previous) => [...previous, component]);
  }, []);

  const updateComponent = useCallback((index, component) => {
    setComponents((previous) =>
      previous.map((existing, componentIndex) =>
        componentIndex === index ? { ...existing, ...component } : existing
      )
    );
  }, []);

  const primaryLabel =
    loading && step === 2
      ? "Generating components… (may take a few seconds)"
      : step === 2
        ? "Generate Components"
        : "Continue";

  const showStaleNotice = step < 3 && project !== null && needsSave;

  return {
    step,
    maxStep,
    intakeForm,
    setIntakeForm,
    errors,
    project,
    components,
    loading,
    error,
    setError,
    derived,
    needsSave,
    hasPricing,
    canGeneratePricing,
    inWorkspace,
    sidebarCollapsed,
    setSidebarCollapsed,
    goToStep,
    goNext,
    goBack,
    reset,
    moveComponent,
    removeComponent,
    addComponent,
    updateComponent,
    primaryLabel,
    showStaleNotice,
    getIntakeOutput,
    approveComponentsAndGenerateDiagrams,
    generatePricing,
  };
}
