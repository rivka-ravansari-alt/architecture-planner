import { useEffect, useId, useState } from "react";
import mermaid from "mermaid";

let mermaidInitialized = false;

function ensureMermaidInit() {
  if (mermaidInitialized) return;
  mermaid.initialize({
    startOnLoad: false,
    theme: "neutral",
    securityLevel: "strict",
    flowchart: { htmlLabels: true, curve: "basis" },
  });
  mermaidInitialized = true;
}

export default function MermaidDiagram({ diagram }) {
  const renderId = useId().replace(/:/g, "");
  const [svgMarkup, setSvgMarkup] = useState("");
  const [failed, setFailed] = useState(false);

  const content = diagram?.content?.trim();

  useEffect(() => {
    if (!content) {
      setSvgMarkup("");
      setFailed(false);
      return undefined;
    }

    let cancelled = false;
    setFailed(false);
    setSvgMarkup("");
    ensureMermaidInit();

    (async () => {
      try {
        const { svg } = await mermaid.render(`mermaid-${renderId}`, content);
        if (!cancelled) setSvgMarkup(svg);
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [content, renderId]);

  if (!content) {
    return <p className="muted doc-empty">No architecture diagram available.</p>;
  }

  if (failed) {
    return (
      <div className="mermaid-diagram-card mermaid-diagram-fallback">
        <p className="mermaid-diagram-fallback-label">
          Diagram preview unavailable — showing source definition:
        </p>
        <pre className="mermaid-diagram-code">
          <code>{content}</code>
        </pre>
      </div>
    );
  }

  return (
    <div className="mermaid-diagram-card">
      <div
        className="mermaid-diagram-scroll"
        aria-label="Architecture diagram"
        dangerouslySetInnerHTML={svgMarkup ? { __html: svgMarkup } : undefined}
      />
    </div>
  );
}
