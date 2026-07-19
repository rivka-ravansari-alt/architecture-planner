export function Spinner({ className = "" }) {
  return <span className={`spinner ${className}`.trim()} aria-hidden />;
}
