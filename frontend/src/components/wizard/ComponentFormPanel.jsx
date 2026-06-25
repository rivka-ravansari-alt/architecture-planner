import { useEffect, useState } from "react";
import { X } from "lucide-react";

import { formatComponentTypeLabel } from "../../constants/componentTypes.js";
import { getCatalogTypeNames } from "../../constants/componentCatalog.js";
import {
  buildComponentFromForm,
  applyTypeDescription,
  componentToForm,
  emptyComponentForm,
  validateComponentForm,
} from "../../utils/componentForm.js";

export default function ComponentFormPanel({
  open,
  mode = "create",
  initialComponent = null,
  existingKeys = new Set(),
  componentCatalog = [],
  onClose,
  onSubmit,
}) {
  const [form, setForm] = useState(emptyComponentForm);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (!open) {
      return;
    }
    setForm(initialComponent ? componentToForm(initialComponent) : emptyComponentForm());
    setErrors({});
  }, [open, initialComponent]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  const catalogTypes =
    componentCatalog.length > 0
      ? componentCatalog.map((entry) => entry.name)
      : getCatalogTypeNames();

  const isEdit = mode === "edit";
  const title = isEdit ? "Edit Component" : "Add Component";
  const submitLabel = isEdit ? "Save changes" : "Add component";

  const updateField = (field, value) => {
    setForm((previous) => ({ ...previous, [field]: value }));
    if (errors[field]) {
      setErrors((previous) => {
        const next = { ...previous };
        delete next[field];
        return next;
      });
    }
  };

  const handleTypeChange = (nextType) => {
    setForm((previous) => applyTypeDescription(previous, nextType));
    if (errors.type || errors.reason) {
      setErrors((previous) => {
        const next = { ...previous };
        delete next.type;
        delete next.reason;
        return next;
      });
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const nextErrors = validateComponentForm(form);
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }
    onSubmit(
      buildComponentFromForm(form, {
        existingKeys,
        currentComponent: initialComponent,
      })
    );
    onClose();
  };

  return (
    <div className="component-form-overlay" role="presentation" onClick={onClose}>
      <aside
        className="component-form-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="component-form-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="component-form-header">
          <div>
            <p className="component-form-eyebrow">Component Review</p>
            <h2 id="component-form-title" className="component-form-title">
              {title}
            </h2>
          </div>
          <button
            type="button"
            className="component-form-close"
            onClick={onClose}
            aria-label="Close"
          >
            <X size={18} strokeWidth={2} />
          </button>
        </header>

        <form className="component-form-body" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="component-name">Component Name (optional)</label>
            <input
              id="component-name"
              type="text"
              placeholder="Defaults to the selected component type"
              value={form.name}
              onChange={(event) => updateField("name", event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="component-type">Component Type</label>
            <select
              id="component-type"
              value={form.type}
              onChange={(event) => handleTypeChange(event.target.value)}
              autoFocus
            >
              {catalogTypes.map((type) => (
                <option key={type} value={type}>
                  {formatComponentTypeLabel(type)}
                </option>
              ))}
            </select>
            <p className="field-hint">Choose from the same catalog used for AI generation.</p>
            {errors.type && <div className="error-text">{errors.type}</div>}
          </div>

          <div className="field">
            <label htmlFor="component-reason">Purpose / Description</label>
            <textarea
              id="component-reason"
              placeholder="Explain what this component does in your architecture."
              value={form.reason}
              onChange={(event) => updateField("reason", event.target.value)}
              rows={4}
            />
            <p className="field-hint">
              Filled automatically from the component type. Edit it to match your project.
            </p>
            {errors.reason && <div className="error-text">{errors.reason}</div>}
          </div>

          <fieldset className="field component-form-status">
            <legend>Requirement Status</legend>
            <div className="option-group">
              <label className="option-check">
                <input
                  type="radio"
                  name="component-optional"
                  checked={!form.optional}
                  onChange={() => updateField("optional", false)}
                />
                <span>Required</span>
              </label>
              <label className="option-check">
                <input
                  type="radio"
                  name="component-optional"
                  checked={form.optional}
                  onChange={() => updateField("optional", true)}
                />
                <span>Optional</span>
              </label>
            </div>
          </fieldset>
        </form>

        <footer className="component-form-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" onClick={handleSubmit}>
            {submitLabel}
          </button>
        </footer>
      </aside>
    </div>
  );
}
