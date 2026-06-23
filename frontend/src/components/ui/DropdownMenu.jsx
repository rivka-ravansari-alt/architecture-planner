import { useEffect, useId, useRef, useState } from "react";
import { MoreVertical } from "lucide-react";

export default function DropdownMenu({ label, items }) {
  const [open, setOpen] = useState(false);
  const menuId = useId();
  const rootRef = useRef(null);

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

  if (!items.length) return null;

  return (
    <div className="dropdown-menu" ref={rootRef}>
      <button
        type="button"
        className="dropdown-menu-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        aria-label={label}
        onClick={() => setOpen((current) => !current)}
      >
        <MoreVertical size={16} strokeWidth={2} aria-hidden="true" />
      </button>
      {open && (
        <div className="dropdown-menu-panel" id={menuId} role="menu">
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              role="menuitem"
              className={`dropdown-menu-item${item.destructive ? " is-destructive" : ""}`}
              onClick={() => {
                setOpen(false);
                item.onClick();
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
