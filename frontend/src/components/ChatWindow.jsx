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
    <>
      <div className="chat-header">
        <div style={{ fontWeight: 600, fontSize: "20px", display: "flex", alignItems: "center", gap: "12px" }}>
          ReelRival Intelligence
          <span className="beta-badge" style={{ fontSize: "12px", padding: "4px 10px" }}>
            DeepSeek-R1
          </span>
        </div>
        <button className="btn-secondary" onClick={onReset}>
          New Comparison
        </button>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <Message key={i} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {messages.length <= 2 && !streaming && (
        <div className="chat-suggestions">
          {SUGGESTIONS.map(s => (
            <button key={s} className="btn-pill" onClick={() => handleSend(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="chat-input-area">
        <input
          className="styled-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder="Ask about hooks, engagement, improvements…"
          disabled={streaming}
          style={{ flex: 1 }}
        />
        <button
          className="btn-primary"
          onClick={() => handleSend()}
          disabled={!input.trim() || streaming}
          style={{ padding: "16px 32px", minWidth: "120px" }}
        >
          {streaming ? "…" : "Send"}
        </button>
      </div>
    </>
  );
}

function Message({ message }) {
  const isUser = message.role === "user";

  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
    }}>
      <div className={`message-bubble ${isUser ? 'message-user' : 'message-assistant'}`} style={message.error ? { border: "1px solid var(--error)", color: "var(--error)" } : {}}>
        {isUser ? (
          <span>{message.content}</span>
        ) : (
          <>
            <ReactMarkdown
              components={{
                p: ({ children }) => <p style={{ marginBottom: "16px" }}>{children}</p>,
                strong: ({ children }) => <strong style={{ color: "white", fontWeight: 600 }}>{children}</strong>,
                code: ({ children }) => (
                  <code style={{
                    background: "rgba(0,0,0,0.3)", padding: "2px 8px",
                    borderRadius: "4px", fontSize: "16px", fontFamily: "monospace",
                    border: "1px solid var(--border)"
                  }}>{children}</code>
                ),
                ul: ({ children }) => <ul style={{ paddingLeft: "24px", marginBottom: "16px" }}>{children}</ul>,
                li: ({ children }) => <li style={{ marginBottom: "6px" }}>{children}</li>
              }}
            >
              {message.content}
            </ReactMarkdown>
            {!message.done && (
              <span style={{
                display: "inline-block", width: "10px", height: "18px",
                background: "var(--accent)", marginLeft: "4px",
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