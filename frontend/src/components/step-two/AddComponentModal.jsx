import { useEffect, useMemo, useRef, useState } from "react";

import { projectApi } from "../../api/projectApi.js";
import ErrorBanner from "../ui/ErrorBanner.jsx";
import Modal from "../ui/Modal.jsx";
import { Spinner } from "../ui/Spinner.jsx";

/**
 * Jira-style dialog for adding a component from the Firestore
 * `architecture_categories` collection.
 *
 * Every category is always available — the same category can be added more than
 * once (e.g. two Compute instances). Metadata (category_id/name/description/type)
 * comes straight from Firestore; a new custom category cannot be created.
 *
 * @param {{
 *   onSubmit: (payload: { category_id: string, explanation: string|null }) => Promise<void>,
 *   onClose: () => void,
 * }} props
 */
export default function AddComponentModal({ onSubmit, onClose }) {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(null);
  const [explanation, setExplanation] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [nameError, setNameError] = useState("");

  const pickerRef = useRef(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const result = await projectApi.listArchitectureCategories();
        if (active) setCategories(result ?? []);
      } catch (err) {
        if (active) setLoadError(err.message || "Could not load categories.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const onClickOutside = (event) => {
      if (pickerRef.current && !pickerRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return categories;
    return categories.filter((category) =>
      category.name.toLowerCase().includes(term)
    );
  }, [categories, query]);

  const handleSelect = (category) => {
    setSelected(category);
    setQuery(category.name);
    setOpen(false);
    setNameError("");
  };

  const handleInputChange = (event) => {
    setQuery(event.target.value);
    setSelected(null);
    setOpen(true);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!selected) {
      setNameError("Select a component from the list.");
      return;
    }
    setSubmitting(true);
    setSubmitError("");
    try {
      await onSubmit({
        category_id: selected.id,
        explanation: explanation.trim() || null,
      });
    } catch (err) {
      setSubmitError(err.message || "Could not add the component.");
      setSubmitting(false);
    }
  };

  const footer = (
    <>
      <button
        type="button"
        className="btn btn-ghost"
        onClick={onClose}
        disabled={submitting}
      >
        Cancel
      </button>
      <button
        type="submit"
        form="add-component-form"
        className="btn btn-primary"
        disabled={submitting || loading || !!loadError}
      >
        {submitting ? "Adding…" : "Add component"}
      </button>
    </>
  );

  return (
    <Modal title="Add component" onClose={onClose} footer={footer}>
      {loading ? (
        <div className="modal-loading">
          <Spinner />
          <p>Loading categories…</p>
        </div>
      ) : loadError ? (
        <ErrorBanner message={loadError} />
      ) : (
        <form id="add-component-form" onSubmit={handleSubmit} noValidate>
          {submitError && <ErrorBanner message={submitError} />}

          <div className="field">
            <label htmlFor="add-component-name">
              Name <span className="required">*</span>
            </label>
            <div className="combobox" ref={pickerRef}>
              <input
                id="add-component-name"
                type="text"
                autoComplete="off"
                placeholder="Search components…"
                value={query}
                onChange={handleInputChange}
                onFocus={() => setOpen(true)}
                aria-expanded={open}
                aria-invalid={!!nameError}
              />
              {open && (
                <ul className="combobox-list" role="listbox">
                  {filtered.length === 0 ? (
                    <li className="combobox-empty">No matching components</li>
                  ) : (
                    filtered.map((category) => (
                      <li key={category.id}>
                        <button
                          type="button"
                          className="combobox-option"
                          role="option"
                          aria-selected={selected?.id === category.id}
                          onClick={() => handleSelect(category)}
                        >
                          <span className="combobox-option-name">
                            {category.name}
                          </span>
                          {category.type && (
                            <span className="combobox-option-type">
                              {category.type}
                            </span>
                          )}
                        </button>
                      </li>
                    ))
                  )}
                </ul>
              )}
            </div>
            {nameError && <p className="error-text">{nameError}</p>}
            {selected?.description && (
              <p className="field-hint">{selected.description}</p>
            )}
          </div>

          <div className="field">
            <label htmlFor="add-component-explanation">Explanation</label>
            <textarea
              id="add-component-explanation"
              placeholder="Why are you adding this component? (optional)"
              value={explanation}
              onChange={(event) => setExplanation(event.target.value)}
            />
          </div>
        </form>
      )}
    </Modal>
  );
}
