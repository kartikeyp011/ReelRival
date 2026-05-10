import axios from "axios";

const BASE = "http://localhost:8000";

export const api = axios.create({ baseURL: BASE });

export async function ingestVideos(urlA, urlB) {
  const res = await api.post("/ingest", { url_a: urlA, url_b: urlB });
  return res.data;
}

export async function resetSession(sessionId) {
  await api.delete(`/session/${sessionId}`);
}

export async function checkHealth() {
  const res = await api.get("/health");
  return res.data;
}

// Streaming chat — calls callback for each token
export async function streamChat(sessionId, message, onToken, onDone, onError) {
  try {
    const response = await fetch(`${BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });

    if (!response.ok) {
      const err = await response.json();
      onError(err.detail || "Chat request failed");
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      onToken(chunk);
    }

    onDone();
  } catch (err) {
    onError(err.message || "Network error");
  }
}