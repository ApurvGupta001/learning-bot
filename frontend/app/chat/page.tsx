"use client";

import { useState } from "react";
import { streamChat } from "@/lib/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  // Hardcoded until POST /sessions creates real sessions (later step).
  const sessionId = "demo";

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);

    // Add an empty assistant message we append streamed tokens into.
    setMessages((m) => [...m, { role: "assistant", content: "" }]);

    await streamChat(sessionId, text, {
      onToken: (tok) =>
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = {
            role: "assistant",
            content: copy[copy.length - 1].content + tok,
          };
          return copy;
        }),
      onError: () =>
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = {
            role: "assistant",
            content:
              "(Backend streaming endpoint not implemented yet — coming in the agent-loop step.)",
          };
          return copy;
        }),
    });

    setBusy(false);
  }

  return (
    <main className="container">
      <h1>Chat</h1>
      <div className="card" style={{ minHeight: 320 }}>
        {messages.length === 0 && (
          <p className="muted">Ask something to start learning…</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.content || <span className="muted">…</span>}
          </div>
        ))}
      </div>

      <div className="row" style={{ marginTop: 16 }}>
        <input
          className="input"
          value={input}
          placeholder="Type a message"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          disabled={busy}
        />
        <button className="btn" onClick={send} disabled={busy}>
          {busy ? "…" : "Send"}
        </button>
      </div>
    </main>
  );
}
