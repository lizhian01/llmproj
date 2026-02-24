export const API_BASE =
  import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function fetchJson(path, options = {}) {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const headers = { ...(options.headers || {}) };

  const isForm = options.body instanceof FormData;
  if (!isForm && options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(url, { ...options, headers });
  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (err) {
      data = null;
    }
  }

  if (!res.ok) {
    const message =
      (data && (data.detail || data.message)) || text || `Request failed (${res.status})`;
    throw new Error(message);
  }

  return data ?? {};
}
