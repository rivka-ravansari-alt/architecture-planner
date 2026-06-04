import { Handle, Position } from "@xyflow/react";
import { getComponentIcon } from "../../../../constants/componentTypes.js";

export default function ArchitectureNode({ data }) {
  const Icon = getComponentIcon(data.componentType);
  const isOptional = data.tag === "optional";

  return (
    <div className="arch-flow-node">
      <Handle type="target" position={Position.Top} className="arch-flow-handle" />
      <div className="arch-flow-node-header">
        <span className="arch-flow-node-icon" aria-hidden="true">
          <Icon size={18} strokeWidth={1.75} />
        </span>
        <span className="arch-flow-node-name">{data.label}</span>
      </div>
      <span className={`arch-flow-node-badge ${isOptional ? "optional" : "required"}`}>
        {isOptional ? "Optional" : "Required"}
      </span>
      <Handle type="source" position={Position.Bottom} className="arch-flow-handle" />
    </div>
  );
}
