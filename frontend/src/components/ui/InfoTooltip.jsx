import { useEffect, useId, useRef, useState } from "react";

/**
 * @param {Object} props
 * @param {string} [props.description]
 * @param {string[]} [props.examples]
 */
export default function InfoTooltip({ description, examples = [] }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const tooltipId = useId();
  const hasHelp = Boolean(description) || examples.length > 0;

  useEffect(() => {
    if (!open) return undefined;

    const handlePointerDown = (event) => {
      if (!rootRef.current?.contains(event.target)) {
        setOpen(false);
      }
    };

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  if (!hasHelp) {
    return null;
  }

  return (
    <span
      ref={rootRef}
      className={`info-tooltip${open ? " is-open" : ""}`}
    >
      <button
        type="button"
        className="info-tooltip-trigger"
        aria-label="More information"
        aria-expanded={open}
        aria-describedby={open ? tooltipId : undefined}
        onClick={() => setOpen((current) => !current)}
      >
        ⓘ
      </button>
      <div id={tooltipId} className="info-tooltip-popover" role="tooltip">
        {description && <p className="info-tooltip-text">{description}</p>}
        {examples.length > 0 && (
          <>
            <p className="info-tooltip-examples-label">Examples:</p>
            <ul className="info-tooltip-examples">
              {examples.map((example) => (
                <li key={example}>{example}</li>
              ))}
            </ul>
          </>
        )}
      </div>
    </span>
  );
}
