import { useEffect, useMemo, useState } from "react";

import { api } from "./api.js";

import { STEPS, DESCRIPTION_MAX_TOKENS, estimateTokenCount } from "./constants.js";

import { deriveArchitecture } from "./recompute.js";

import Sidebar from "./components/Sidebar.jsx";

import StepProjectDetails from "./components/StepProjectDetails.jsx";

import StepRequirements from "./components/StepRequirements.jsx";

import ArchitectureWorkspace from "./components/ArchitectureWorkspace.jsx";



const STEP_SUBTITLES = [

  "Tell us about the application you want to plan.",

  "Answer a few questions so we can determine the right components.",

  "Review your AI-generated architecture document and refine the plan.",

];



const EMPTY_FORM = {

  name: "",

  description: "",

  project_types: [],

  stage: "mvp",

  expected_users: "100",

};



const EMPTY_ANSWERS = {

  auth: false,

  file_upload: false,

  background_processing: false,

  dashboards: false,

  ai: false,

  payments: false,

  include_edge_cases: false,

};



export default function App() {

  const [step, setStep] = useState(1);

  // The furthest step the user has unlocked. Steps up to and including this can

  // be revisited freely; later steps stay locked until reached sequentially.

  const [maxStep, setMaxStep] = useState(1);

  const [projectTypes, setProjectTypes] = useState([]);

  const [form, setForm] = useState(EMPTY_FORM);

  const [answers, setAnswers] = useState(EMPTY_ANSWERS);

  const [errors, setErrors] = useState({});

  const [project, setProject] = useState(null);

  const [components, setComponents] = useState([]);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState(null);



  // Snapshot of the inputs (project details + requirements) used for the last

  // successful generation. Used to detect when the architecture is stale and

  // must be regenerated before showing the output steps.

  const [generatedKey, setGeneratedKey] = useState(null);



  // User can move AI-suggested components between Required and Optional.

  const moveComponent = (index, optional) => {

    setComponents((prev) =>

      prev.map((c, i) => (i === index ? { ...c, optional } : c))

    );

  };



  const derived = useMemo(

    () => (project ? deriveArchitecture(project, components) : null),

    [project, components]

  );



  // A stable fingerprint of the current inputs. When this no longer matches the

  // last generated snapshot, the architecture needs to be regenerated.

  const inputKey = useMemo(

    () => JSON.stringify({ form, answers }),

    [form, answers]

  );



  const needsGeneration = project === null || generatedKey !== inputKey;



  useEffect(() => {

    api

      .getProjectTypes()

      .then(setProjectTypes)

      .catch((e) => setError(e.message));

  }, []);



  const validateStep1 = () => {

    const next = {};

    if (!form.name.trim()) next.name = "Project name is required.";

    if (!form.description.trim()) next.description = "Project description is required.";

    else if (estimateTokenCount(form.description) > DESCRIPTION_MAX_TOKENS) {

      next.description = `Project description must be ${DESCRIPTION_MAX_TOKENS} tokens or fewer.`;

    }

    if (form.project_types.length === 0) next.project_types = "Select at least one project type.";

    setErrors(next);

    return Object.keys(next).length === 0;

  };



  // Jump to an already-unlocked step (used by the stepper, sidebar, and Back).

  // Forward jumps to steps that haven't been completed yet are not allowed here;

  // the user must reach them sequentially via Continue. Revisiting the workspace

  // regenerates the plan when the inputs have changed.

  const goToStep = async (target) => {

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

  };



  // Sequential forward navigation via the Continue / Generate button. This is

  // the only path that unlocks a not-yet-completed step.

  const goNext = async () => {

    setError(null);

    if (loading) return;



    if (step === 1) {

      if (!validateStep1()) return;

      unlockAndGo(2);

    } else if (step === 2) {

      if (!validateStep1()) {

        setStep(1);

        return;

      }

      if (needsGeneration) await generate(3);

      else unlockAndGo(3);

    }

  };



  const goBack = () => {

    if (step > 1) goToStep(step - 1);

  };



  const unlockAndGo = (target) => {

    setMaxStep((m) => Math.max(m, target));

    setStep(target);

  };



  const generate = async (target = 3) => {

    setLoading(true);

    setError(null);

    try {

      const created = await api.createProject({ ...form, answers });

      const generated = await api.generate(created.id);

      setProject(generated);

      setComponents(generated.components.map((c) => ({ ...c })));

      setGeneratedKey(inputKey);

      setMaxStep((m) => Math.max(m, target));

      setStep(target);

    } catch (e) {

      setError(e.message);

    } finally {

      setLoading(false);

    }

  };



  const reset = () => {

    setForm(EMPTY_FORM);

    setAnswers(EMPTY_ANSWERS);

    setProject(null);

    setComponents([]);

    setGeneratedKey(null);

    setErrors({});

    setError(null);

    setMaxStep(1);

    setStep(1);

  };



  const primaryLabel =

    step === 2 && needsGeneration ? "Generate Architecture" : "Continue";



  const showStaleNotice = step < 3 && project !== null && needsGeneration;

  const inWorkspace = step === 3 && project;

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    if (inWorkspace) {
      setSidebarCollapsed(true);
    } else {
      setSidebarCollapsed(false);
    }
  }, [inWorkspace]);

  const exitWorkspace = () => goToStep(2);

  return (

    <div className={`app-shell ${inWorkspace ? "focus-mode" : ""}`}>

      <Sidebar
        current={step}
        maxStep={maxStep}
        onStepClick={goToStep}
        loading={loading}
        collapsed={inWorkspace && sidebarCollapsed}
        focusMode={inWorkspace}
        onToggleCollapse={() => setSidebarCollapsed((c) => !c)}
      />

      <main className="main">

        {!inWorkspace && (
        <header className="topbar">

          <div className="topbar-text">

            <h1>{STEPS[step - 1]}</h1>

            <p>{STEP_SUBTITLES[step - 1]}</p>

          </div>

          {(project !== null || step > 1) && (

            <button

              className="btn btn-ghost btn-reset"

              onClick={reset}

              disabled={loading}

              title="Clear all answers and start a new plan"

            >

              Reset Project

            </button>

          )}

        </header>
        )}

        <div className={`content ${inWorkspace ? "content-workspace content-focus" : ""}`}>

          {error && <div className="error-banner">{error}</div>}



          {showStaleNotice && (

            <div className="info-note">

              You've changed your inputs. The architecture, cloud mapping, risks,

              recommendations, and cost estimates will be regenerated when you

              open the Architecture Document.

            </div>

          )}



          {step === 1 && (

            <StepProjectDetails

              form={form}

              setForm={setForm}

              projectTypes={projectTypes}

              errors={errors}

            />

          )}

          {step === 2 && <StepRequirements answers={answers} setAnswers={setAnswers} />}

          {inWorkspace && (

            <ArchitectureWorkspace

              project={project}

              projectTypes={projectTypes}

              components={components}

              onMove={moveComponent}

              risks={derived.risks}

              recommendations={derived.recommendations}

              costs={derived.costs}

              onExit={exitWorkspace}

              onReset={reset}

              onToggleAppSidebar={() => setSidebarCollapsed((c) => !c)}

              appSidebarCollapsed={sidebarCollapsed}

            />

          )}



          {!inWorkspace && (

            <div className="actions">

              {step > 1 ? (

                <button className="btn btn-ghost" onClick={goBack} disabled={loading}>

                  Back

                </button>

              ) : (

                <span />

              )}



              {step < 3 && (

                <button className="btn btn-primary" onClick={goNext} disabled={loading}>

                  {loading && <span className="spinner" />}

                  {primaryLabel}

                </button>

              )}

            </div>

          )}

        </div>

      </main>

    </div>

  );

}


