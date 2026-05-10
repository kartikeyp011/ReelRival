import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { streamChat } from "../api";

export default function ChatWindow({ sessionId, videoA, videoB, onReset }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: `I've analyzed **${videoA?.title}** and **${videoB?.title}**. Ask me anything — hooks, engagement, structure, improvements.`,
      done: true,
    }
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef(null);

  const SUGGESTIONS = [
    "Which video has a stronger hook?",
    "Compare engagement rates",
    "What should Video B improve?",
    "Which opening is more compelling?",
  ];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text) {
    const msg = text || input.trim();
    if (!msg || streaming) return;
    setInput("");
    setStreaming(true);

    setMessages(prev => [
      ...prev,
      { role: "user", content: msg, done: true },
      { role: "assistant", content: "", done: false },
    ]);

    await streamChat(
      sessionId,
      msg,
      (token) => {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: updated[updated.length - 1].content + token,
          };
          return updated;
        });
      },
      () => {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            done: true,
          };
          return updated;
        });
        setStreaming(false);
      },
      (err) => {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: `⚠ Error: ${err}`,
            done: true,
            error: true,
          };
          return updated;
        });
        setStreaming(false);
      }
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>

      {/* Header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "14px 20px", borderBottom: "1px solid var(--border)",
        background: "var(--surface)",
      }}>
        <div style={{ fontWeight: 600, fontSize: "14px" }}>
          ReelRival Chat
          <span style={{ marginLeft: "10px", fontSize: "12px", color: "var(--text-muted)", fontWeight: 400 }}>
            DeepSeek-R1 · RAG
          </span>
        </div>
        <button
          onClick={onReset}
          style={{
            fontSize: "12px", color: "var(--text-muted)",
            padding: "5px 12px", borderRadius: "6px",
            border: "1px solid var(--border)", background: "transparent",
          }}
        >
          New Comparison
        </button>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1, overflowY: "auto", padding: "20px",
        display: "flex", flexDirection: "column", gap: "16px",
      }}>
        {messages.map((msg, i) => (
          <Message key={i} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 2 && !streaming && (
        <div style={{
          display: "flex", gap: "8px", flexWrap: "wrap",
          padding: "0 20px 12px",
        }}>
          {SUGGESTIONS.map(s => (
            <button key={s} onClick={() => handleSend(s)} style={{
              fontSize: "12px", padding: "6px 12px",
              background: "var(--surface-2)", border: "1px solid var(--border)",
              borderRadius: "999px", color: "var(--text-muted)",
              transition: "all 0.15s",
            }}
              onMouseEnter={e => { e.target.style.borderColor = "var(--accent)"; e.target.style.color = "var(--accent)"; }}
              onMouseLeave={e => { e.target.style.borderColor = "var(--border)"; e.target.style.color = "var(--text-muted)"; }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{
        padding: "16px 20px", borderTop: "1px solid var(--border)",
        background: "var(--surface)", display: "flex", gap: "10px",
      }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder="Ask about hooks, engagement, improvements…"
          disabled={streaming}
          style={{
            flex: 1, background: "var(--surface-2)", border: "1px solid var(--border)",
            borderRadius: "var(--radius)", padding: "11px 14px",
            color: "var(--text)", fontSize: "14px", outline: "none",
          }}
          onFocus={e => e.target.style.borderColor = "var(--accent)"}
          onBlur={e => e.target.style.borderColor = "var(--border)"}
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || streaming}
          style={{
            background: (!input.trim() || streaming) ? "var(--surface-2)" : "var(--accent)",
            color: (!input.trim() || streaming) ? "var(--text-faint)" : "white",
            padding: "11px 20px", borderRadius: "var(--radius)",
            fontWeight: 600, fontSize: "14px", transition: "all 0.15s",
            cursor: (!input.trim() || streaming) ? "not-allowed" : "pointer",
          }}
        >
          {streaming ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}

function Message({ message }) {
  const isUser = message.role === "user";

  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
    }}>
      <div style={{
        maxWidth: "80%",
        background: isUser ? "var(--accent)" : "var(--surface)",
        border: isUser ? "none" : "1px solid var(--border)",
        borderRadius: isUser ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
        padding: "12px 16px",
        fontSize: "14px",
        lineHeight: "1.65",
        color: message.error ? "var(--error)" : "var(--text)",
      }}>
        {isUser ? (
          <span>{message.content}</span>
        ) : (
          <>
            <ReactMarkdown
              components={{
                p: ({ children }) => <p style={{ marginBottom: "8px" }}>{children}</p>,
                strong: ({ children }) => <strong style={{ color: "white", fontWeight: 600 }}>{children}</strong>,
                code: ({ children }) => (
                  <code style={{
                    background: "var(--surface-2)", padding: "1px 6px",
                    borderRadius: "4px", fontSize: "13px",
                  }}>{children}</code>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
            {!message.done && (
              <span style={{
                display: "inline-block", width: "8px", height: "14px",
                background: "var(--accent)", marginLeft: "3px",
                animation: "blink 1s steps(2) infinite",
                verticalAlign: "text-bottom",
              }} />
            )}
          </>
        )}
      </div>
    </div>
  );
}