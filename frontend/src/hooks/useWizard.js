import { useCallback, useEffect, useMemo, useState } from "react";

import { api } from "../api/index.js";
import { EMPTY_ANSWERS, EMPTY_FORM } from "../constants/wizard.js";
import { deriveArchitecture } from "../features/architecture/utils/deriveArchitecture.js";
import { buildInputKey, validateProjectForm } from "../utils/validation.js";

export function useWizard() {
  const [step, setStep] = useState(1);
  const [maxStep, setMaxStep] = useState(1);
  const [form, setForm] = useState(EMPTY_FORM);
  const [answers, setAnswers] = useState(EMPTY_ANSWERS);
  const [errors, setErrors] = useState({});
  const [project, setProject] = useState(null);
  const [components, setComponents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [generatedKey, setGeneratedKey] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const inputKey = useMemo(() => buildInputKey(form, answers), [form, answers]);
  const needsGeneration = project === null || generatedKey !== inputKey;
  const inWorkspace = step === 3 && project;

  const derived = useMemo(
    () => (project ? deriveArchitecture(project, components) : null),
    [project, components]
  );

  useEffect(() => {
    setSidebarCollapsed(Boolean(inWorkspace));
  }, [inWorkspace]);

  const validateStep1 = useCallback(() => {
    const nextErrors = validateProjectForm(form);
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }, [form]);

  const unlockAndGo = useCallback((target) => {
    setMaxStep((current) => Math.max(current, target));
    setStep(target);
  }, []);

  const generate = useCallback(
    async (target = 3) => {
      setLoading(true);
      setError(null);
      try {
        const created = await api.createProject({ ...form, answers });
        const generated = await api.generate(created.id);
        setProject(generated);
        setComponents(generated.components.map((component) => ({ ...component })));
        setGeneratedKey(inputKey);
        setMaxStep((current) => Math.max(current, target));
        setStep(target);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [form, answers, inputKey]
  );

  const goToStep = useCallback(
    async (target) => {
      setError(null);
      if (target === step || loading) return;
      if (target < 1 || target > maxStep) return;

      if (target >= 3) {
        if (!validateStep1()) {
          setStep(1);
          return;
        }
        if (needsGeneration) {
          await generate(target);
          return;
        }
      }

      setStep(target);
    },
    [step, loading, maxStep, validateStep1, needsGeneration, generate]
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
      if (needsGeneration) await generate(3);
      else unlockAndGo(3);
    }
  }, [step, loading, validateStep1, unlockAndGo, needsGeneration, generate]);

  const goBack = useCallback(() => {
    if (step > 1) goToStep(step - 1);
  }, [step, goToStep]);

  const reset = useCallback(() => {
    setForm(EMPTY_FORM);
    setAnswers(EMPTY_ANSWERS);
    setProject(null);
    setComponents([]);
    setGeneratedKey(null);
    setErrors({});
    setError(null);
    setMaxStep(1);
    setStep(1);
  }, []);

  const moveComponent = useCallback((index, optional) => {
    setComponents((previous) =>
      previous.map((component, componentIndex) =>
        componentIndex === index ? { ...component, optional } : component
      )
    );
  }, []);

  const primaryLabel = step === 2 && needsGeneration ? "Generate Architecture" : "Continue";
  const showStaleNotice = step < 3 && project !== null && needsGeneration;

  return {
    step,
    maxStep,
    form,
    setForm,
    answers,
    setAnswers,
    errors,
    project,
    components,
    loading,
    error,
    setError,
    derived,
    needsGeneration,
    inWorkspace,
    sidebarCollapsed,
    setSidebarCollapsed,
    goToStep,
    goNext,
    goBack,
    reset,
    moveComponent,
    primaryLabel,
    showStaleNotice,
  };
}
