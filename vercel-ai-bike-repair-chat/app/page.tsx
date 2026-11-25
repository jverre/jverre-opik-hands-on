"use client";

import { useState } from "react";
import { useChat } from "@ai-sdk/react";

// useChat generates a chat id and posts it with the full history on every turn;
// the route forwards it as the Opik thread id.
export default function WorkshopChat() {
  const [input, setInput] = useState("");
  const { messages, sendMessage, status } = useChat();
  const busy = status === "submitted" || status === "streaming";

  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: "2rem 1rem", display: "flex", flexDirection: "column", minHeight: "100vh", boxSizing: "border-box" }}>
      <h1 style={{ fontSize: "1.25rem", marginBottom: "0.25rem" }}>Spoke, the Cobblestone Cycle Co-op assistant</h1>
      <p style={{ color: "#5b6455", marginTop: 0, fontSize: "0.9rem" }}>
        Ask about squeaks, brakes, tyres or gears. Replies stream in, and every turn becomes a trace in Opik.
      </p>

      <div style={{ flex: 1 }}>
        {messages.map((message) => (
          <div key={message.id} style={{ margin: "0.75rem 0", display: "flex", justifyContent: message.role === "user" ? "flex-end" : "flex-start" }}>
            <div
              style={{
                maxWidth: "85%",
                padding: "0.6rem 0.9rem",
                borderRadius: 12,
                background: message.role === "user" ? "#2e7d32" : "#ffffff",
                color: message.role === "user" ? "#ffffff" : "#1d2419",
                border: message.role === "user" ? "none" : "1px solid #dfe5d8",
                whiteSpace: "pre-wrap",
                lineHeight: 1.45,
              }}
            >
              {message.parts.map((part, i) => (part.type === "text" ? <span key={i}>{part.text}</span> : null))}
            </div>
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!input.trim() || busy) return;
          sendMessage({ text: input });
          setInput("");
        }}
        style={{ display: "flex", gap: "0.5rem", paddingTop: "1rem" }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="My chain squeaks when I pedal uphill..."
          style={{ flex: 1, padding: "0.6rem 0.9rem", borderRadius: 10, border: "1px solid #c9d1c0", fontSize: "1rem", outline: "none" }}
        />
        <button type="submit" disabled={busy} style={{ padding: "0.6rem 1.1rem", borderRadius: 10, border: "none", background: busy ? "#9aa594" : "#2e7d32", color: "#fff", fontSize: "1rem" }}>
          Send
        </button>
      </form>
    </main>
  );
}
