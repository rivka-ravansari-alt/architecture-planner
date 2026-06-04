import { Handle, Position } from "@xyflow/react";

export default function GroupNode({ data }) {
  return (
    <div className="arch-flow-group">
      <span className="arch-flow-group-label">{data.label}</span>
    </div>
  );
}
