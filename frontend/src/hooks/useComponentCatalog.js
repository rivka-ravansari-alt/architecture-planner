import { useEffect, useState } from "react";

import { api } from "../api/index.js";
import { setComponentCatalog } from "../constants/componentCatalog.js";

export function useComponentCatalog() {
  const [componentCatalog, setComponentCatalogState] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getComponentCatalog()
      .then((entries) => {
        if (cancelled) {
          return;
        }
        setComponentCatalog(entries);
        setComponentCatalogState(entries);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { componentCatalog, error };
}
