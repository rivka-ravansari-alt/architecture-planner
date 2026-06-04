import { useEffect, useState } from "react";

import { api } from "../api/index.js";

export function useProjectTypes() {
  const [projectTypes, setProjectTypes] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getProjectTypes()
      .then((types) => {
        if (!cancelled) setProjectTypes(types);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { projectTypes, error };
}
