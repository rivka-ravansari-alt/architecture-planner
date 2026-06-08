const BASE = "/api";
const DEFAULT_TIMEOUT_MS = 30_000;
const GENERATE_TIMEOUT_MS = 330_000;

export async function apiRequest(path, options = {}) {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, ...fetchOptions } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${BASE}${path}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json", ...fetchOptions.headers },
      ...fetchOptions,
      signal: controller.signal,
    });

    if (!response.ok) {
      let detail = `Request failed (${response.status})`;
      try {
        const body = await response.json();
        if (body.detail) {
          detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
        }
      } catch {
        // ignore parse errors
      }
      throw new Error(detail);
    }

    if (response.status === 204) return null;
    return response.json();
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Request timed out. The AI generation may still be running — try again in a moment.");
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export { GENERATE_TIMEOUT_MS };
