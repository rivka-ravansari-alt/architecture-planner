export default function Badge({ variant = "required", children }) {
  return <span className={`badge ${variant}`}>{children}</span>;
}
