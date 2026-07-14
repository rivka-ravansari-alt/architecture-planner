import { useCallback, useEffect, useRef, useState } from "react";

import { projectApi } from "../../api/projectApi.js";
import ErrorBanner from "../ui/ErrorBanner.jsx";
import { Spinner } from "../ui/Spinner.jsx";
import AddComponentModal from "./AddComponentModal.jsx";
import ComponentReviewCard from "./ComponentReviewCard.jsx";

/**
 * Step 2: generate and review the selected architecture components.
 *
 * @param {{ projectId: string, onBack?: () => void }} props
 */
export default function ComponentSelectionScreen({ projectId, onBack }) {
  const [selection, setSelection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [removingId, setRemovingId] = useState(null);
  const [addOpen, setAddOpen] = useState(false);
  const generateRequestRef = useRef(0);

  const generate = useCallback(async () => {
    const requestId = ++generateRequestRef.current;
    setLoading(true);
    setError("");
    try {
      const result = await projectApi.generateArchitectureComponents(projectId);
      if (requestId !== generateRequestRef.current) return;
      setSelection(result);
    } catch (err) {
      if (requestId !== generateRequestRef.current) return;
      setError(err.message || "Could not generate components. Please try again.");
    } finally {
      if (requestId === generateRequestRef.current) {
        setLoading(false);
      }
    }
  }, [projectId]);

  useEffect(() => {
    let active = true;

    (async () => {
      setLoading(true);
      setError("");
      try {
        const existing = await projectApi.getArchitectureSelection(projectId);
        if (!active) return;
        setSelection(existing);
      } catch (err) {
        if (!active) return;
        const message = err.message || "";
        if (!message.includes("No component selection exists")) {
          setError(message || "Could not load components. Please try again.");
          setLoading(false);
          return;
        }
        await generate();
      } finally {
        if (active) setLoading(false);
      }
    })();

    return () => {
      active = false;
      generateRequestRef.current += 1;
    };
  }, [projectId, generate]);

  const handleAdd = useCallback(
    async (payload) => {
      if (!selection?.selection_id) return;
      setActionError("");
      const result = await projectApi.addArchitectureComponent(projectId, {
        selection_id: selection.selection_id,
        ...payload,
      });
      setSelection(result);
      setAddOpen(false);
    },
    [projectId, selection?.selection_id]
  );

  const handleRemove = useCallback(
    async (component) => {
      if (!selection?.selection_id) return;
      setActionError("");
      setRemovingId(component.instance_id);
      try {
        const result = await projectApi.removeArchitectureComponent(
          projectId,
          selection.selection_id,
          component.instance_id
        );
        setSelection(result);
      } catch (err) {
        setActionError(err.message || "Could not remove the component.");
      } finally {
        setRemovingId(null);
      }
    },
    [projectId, selection?.selection_id]
  );

  if (loading) {
    return (
      <div className="component-review-loading">
        <Spinner />
        <p>Selecting architecture components for your application…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="component-review">
        <ErrorBanner message={error} />
        <div className="actions">
          {onBack && (
            <button type="button" className="btn btn-ghost" onClick={onBack}>
              Back
            </button>
          )}
          <button type="button" className="btn btn-primary" onClick={generate}>
            Try again
          </button>
        </div>
      </div>
    );
  }

  const selected = selection?.selected ?? [];

  return (
    <div className="component-review">
      <header className="component-review-header">
        <h1>Architecture components</h1>
        <p className="subtitle">
          Based on your application, we recommend the following components.
        </p>
      </header>

      {actionError && <ErrorBanner message={actionError} />}

      <section className="component-review-section">
        <div className="component-review-section-head">
          <h2>
            Selected components <span className="count">{selected.length}</span>
          </h2>
          <button
            type="button"
            className="btn btn-primary btn-add-component"
            onClick={() => {
              setActionError("");
              setAddOpen(true);
            }}
          >
            + Add component
          </button>
        </div>
        <div className="component-review-grid">
          {selected.map((component) => (
            <ComponentReviewCard
              key={component.instance_id}
              component={component}
              variant="selected"
              onRemove={handleRemove}
              removing={removingId === component.instance_id}
            />
          ))}
        </div>
      </section>

      {onBack && (
        <div className="actions">
          <button type="button" className="btn btn-ghost" onClick={onBack}>
            Back
          </button>
          <span />
        </div>
      )}

      {addOpen && (
        <AddComponentModal onSubmit={handleAdd} onClose={() => setAddOpen(false)} />
      )}
    </div>
  );
}
