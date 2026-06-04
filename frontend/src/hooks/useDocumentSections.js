import { useCallback, useEffect, useRef, useState } from "react";

import { DOCUMENT_SECTIONS } from "../constants/document.js";

const DEFAULT_EXPANDED = Object.fromEntries(DOCUMENT_SECTIONS.map((section) => [section.id, true]));

export function useDocumentSections() {
  const [activeSection, setActiveSection] = useState("overview");
  const [expandedSections, setExpandedSections] = useState(DEFAULT_EXPANDED);
  const scrollRef = useRef(null);
  const sectionRefs = useRef({});

  const registerSection = useCallback((id, node) => {
    if (node) sectionRefs.current[id] = node;
  }, []);

  useEffect(() => {
    const root = scrollRef.current;
    if (!root) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]?.target?.id) {
          setActiveSection(visible[0].target.id);
        }
      },
      { root, rootMargin: "-20% 0px -55% 0px", threshold: [0, 0.25, 0.5, 1] }
    );

    for (const section of DOCUMENT_SECTIONS) {
      const node = sectionRefs.current[section.id];
      if (node) observer.observe(node);
    }

    return () => observer.disconnect();
  }, [expandedSections]);

  const scrollToSection = useCallback((id) => {
    setExpandedSections((previous) => ({ ...previous, [id]: true }));
    requestAnimationFrame(() => {
      const node = sectionRefs.current[id];
      if (node) {
        node.scrollIntoView({ behavior: "smooth", block: "start" });
        setActiveSection(id);
      }
    });
  }, []);

  const toggleSection = useCallback((id) => {
    setExpandedSections((previous) => ({ ...previous, [id]: !previous[id] }));
  }, []);

  return {
    activeSection,
    expandedSections,
    scrollRef,
    registerSection,
    scrollToSection,
    toggleSection,
  };
}
