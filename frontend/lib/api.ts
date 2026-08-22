// Thin client for the backend API.
//
// Chat responses are streamed. We POST the user's message and read the response
// body as a stream of Server-Sent-Events-style chunks ("data: ...\n\n").
// EventSource only supports GET, so we use fetch + a ReadableStream reader,
// which lets us POST and still stream tokens as they arrive.

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<unknown> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`health check failed: ${res.status}`);
  return res.json();
}

export interface StreamHandlers {
  onToken: (text: string) => void;
  onDone?: () => void;
  onError?: (err: unknown) => void;
}

/**
 * Stream an assistant reply for a message in a session.
 *
 * NOTE: the backend `/sessions/{id}/message` route is added in a later step.
 * The parsing loop below is ready for it: each SSE frame is `data: <text>\n\n`,
 * and a `data: [DONE]` frame ends the stream.
 */
export async function streamChat(
  sessionId: string,
  content: string,
  handlers: StreamHandlers,
): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    if (!res.ok || !res.body) {
      throw new Error(`stream failed: ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Split on SSE frame boundaries.
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";
      for (const frame of frames) {
        const line = frame.replace(/^data:\s?/, "");
        if (!line) continue;
        if (line === "[DONE]") {
          handlers.onDone?.();
          return;
        }
        // Each token is JSON-encoded so newlines can't break SSE framing.
        try {
          handlers.onToken(JSON.parse(line) as string);
        } catch {
          handlers.onToken(line);
        }
      }
    }
    handlers.onDone?.();
  } catch (err) {
    handlers.onError?.(err);
  }
}
