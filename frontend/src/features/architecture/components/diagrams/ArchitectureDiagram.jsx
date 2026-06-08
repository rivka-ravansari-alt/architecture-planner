import { useEffect, useMemo } from "react";
import { Background, ReactFlow, ReactFlowProvider, useReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import ArchitectureNode from "./ArchitectureNode.jsx";
import GroupNode from "./GroupNode.jsx";
import { buildFlowGraph } from "./diagramUtils.js";

const nodeTypes = { architecture: ArchitectureNode, tierGroup: GroupNode };
const MAX_CANVAS_WIDTH = 860;

function FitViewOnLoad({ trigger }) {
  const { fitView } = useReactFlow();

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      fitView({ padding: 0.14, maxZoom: 1, minZoom: 0.9, duration: 150 });
    });
    return () => cancelAnimationFrame(frame);
  }, [trigger, fitView]);

  return null;
}

function ArchitectureDiagramCanvas({ diagram, components, diagramType }) {
  const graph = useMemo(
    () => buildFlowGraph(diagram, components, diagramType),
    [diagram, components, diagramType]
  );

  const canvasSize = useMemo(() => {
    if (!graph) return null;
    const { bounds } = graph;
    const width = Math.min(bounds.width, MAX_CANVAS_WIDTH);
    const height = bounds.height;
    return {
      width,
      height,
      key: `${width}-${height}-${graph.nodes.length}-${graph.edges.length}`,
    };
  }, [graph]);

  if (!graph || !canvasSize) {
    return <p className="muted doc-empty">No architecture diagram available.</p>;
  }

  const { nodes, edges } = graph;

  return (
    <div
      className="arch-flow-diagram-viewport"
      style={{ width: canvasSize.width, height: canvasSize.height }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag
        zoomOnScroll
        proOptions={{ hideAttribution: true }}
      >
        <FitViewOnLoad trigger={canvasSize.key} />
        <Background color="#e2e8f0" gap={20} size={1} />
      </ReactFlow>
    </div>
  );
}

export default function ArchitectureDiagram({ diagram, components, diagramType = "high_level" }) {
  if (diagram?.type === "mermaid") {
    return null;
  }

  return (
    <ReactFlowProvider>
      <ArchitectureDiagramCanvas
        diagram={diagram}
        components={components}
        diagramType={diagramType}
      />
    </ReactFlowProvider>
  );
}
