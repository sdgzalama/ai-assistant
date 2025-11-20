import React, { useState, useRef, useEffect } from "react";

function App() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [category, setCategory] = useState("general");
  const bottomRef = useRef(null);

  //DEPLOY BACKEND ON RENDER:
  const API_BASE = "https://ai-assistant-media-laws.onrender.com";
  
  // const API_BASE = "http://localhost:8000";


  const categories = [
    { value: "general", label: "General Media" },
    { value: "laws", label: "Media Laws" },
    { value: "ethics", label: "Journalism Ethics" },
    { value: "strategy", label: "Content Strategy" },
    { value: "analysis", label: "Market Analysis" }
  ];

  const formatTime = (timestamp) => {
    if (typeof timestamp === "string") timestamp = new Date(timestamp);
    return timestamp.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const sendMessage = async () => {
    if (!message.trim()) return;

    setLoading(true);
    const userMessage = message;

    // Add user message immediately
    setChatHistory((prev) => [
      ...prev,
      {
        role: "user",
        text: userMessage,
        ts: new Date(),
        category,
      },
    ]);

    setMessage("");

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          category,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Add AI reply
      setChatHistory((prev) => [
        ...prev,
        {
          role: "ai",
          text: data.reply,
          ts: new Date(),
          language: data.language_detected,
          category: data.category,
        },
      ]);
    } catch (error) {
      console.error("Error:", error);
      setChatHistory((prev) => [
        ...prev,
        {
          role: "ai",
          text: "Sorry, I encountered an error. Please try again.",
          ts: new Date(),
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const clearCurrentChat = () => {
    setChatHistory([]);
  };

  return (
    <div
      style={{
        backgroundColor: "#f5f6fa",
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "20px",
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 800,
          background: "#fff",
          borderRadius: 16,
          boxShadow: "0 8px 30px rgba(0,0,0,0.12)",
          display: "flex",
          flexDirection: "column",
          height: "90vh",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "20px 24px",
            background: "linear-gradient(135deg, #1a73e8 0%, #4285f4 100%)",
            color: "#fff",
            borderTopLeftRadius: 16,
            borderTopRightRadius: 16,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>
              Hamasa Media AI Assistant
            </h1>
            <p style={{ margin: "4px 0 0 0", opacity: 0.9, fontSize: 14 }}>
              Specialized in Tanzanian media laws and press freedom
            </p>
          </div>

          <button
            onClick={clearCurrentChat}
            style={{
              background: "rgba(255,255,255,0.2)",
              border: "none",
              color: "white",
              padding: "8px 16px",
              borderRadius: 8,
              cursor: "pointer",
              fontSize: 14,
              fontWeight: 500,
            }}
          >
            Clear Chat
          </button>
        </div>

        {/* Category Selector */}
        <div
          style={{
            padding: "12px 20px",
            borderBottom: "1px solid #eaeaea",
            background: "#f8f9fa",
          }}
        >
          <label
            style={{ fontSize: 14, fontWeight: 500, marginRight: 10 }}
          >
            Category:
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            style={{
              padding: "6px 12px",
              borderRadius: 6,
              border: "1px solid #ddd",
              fontSize: 14,
              background: "white",
            }}
          >
            {categories.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
        </div>

        {/* Chat Area */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "20px",
            background: "#f9fafc",
          }}
        >
          {/* Empty screen welcome message */}
          {chatHistory.length === 0 && (
            <div style={{ textAlign: "center", marginTop: "40%", color: "#666" }}>
              <h3 style={{ color: "#1a73e8" }}>Welcome to Hamasa Media AI</h3>
              <p>Ask about Tanzanian media laws or content strategy.</p>
              <div style={{ marginTop: 20, fontSize: 14, color: "#888" }}>
                <div>Example:</div>
                <div>"What is the Media Services Act 2016?"</div>
                <div>"How do journalists maintain ethics?"</div>
              </div>
            </div>
          )}

          {/* Chat Messages */}
          {chatHistory.map((msg, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                marginBottom: 16,
              }}
            >
              <div
                style={{
                  backgroundColor: msg.role === "user" ? "#1a73e8" : "#ffffff",
                  color: msg.role === "user" ? "#fff" : "#333",
                  padding: "12px 16px",
                  borderRadius:
                    msg.role === "user"
                      ? "18px 18px 6px 18px"
                      : "18px 18px 18px 6px",
                  maxWidth: "70%",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                  border: msg.role === "ai" ? "1px solid #eaeaea" : "none",
                }}
              >
                {msg.text}
                <div
                  style={{
                    fontSize: 11,
                    textAlign: "right",
                    opacity: 0.6,
                    marginTop: 6,
                  }}
                >
                  {formatTime(msg.ts)}
                </div>
              </div>
            </div>
          ))}

          {/* Loading dots */}
          {loading && (
            <div style={{ marginBottom: 16 }}>
              <div
                style={{
                  backgroundColor: "#ffffff",
                  padding: "12px 16px",
                  borderRadius: "18px 18px 18px 6px",
                  border: "1px solid #eaeaea",
                  width: "70px",
                }}
              >
                <div style={{ display: "flex", gap: 6 }}>
                  <div className="dot"></div>
                  <div className="dot"></div>
                  <div className="dot"></div>
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input Section */}
        <div
          style={{
            borderTop: "1px solid #eaeaea",
            padding: "16px 20px",
            background: "#fff",
          }}
        >
          <div style={{ display: "flex", gap: 12 }}>
            <input
              style={{
                flex: 1,
                padding: "12px 16px",
                border: "1px solid #ddd",
                borderRadius: 12,
                fontSize: 15,
              }}
              type="text"
              placeholder="Ask your question…"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) =>
                e.key === "Enter" && !loading && sendMessage()
              }
            />
            <button
              style={{
                backgroundColor: "#1a73e8",
                color: "#fff",
                padding: "12px 24px",
                borderRadius: 12,
                border: "none",
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading || !message.trim() ? 0.6 : 1,
              }}
              onClick={sendMessage}
              disabled={loading || !message.trim()}
            >
              {loading ? "Sending..." : "Send"}
            </button>
          </div>
        </div>
      </div>

      {/* Animation */}
      <style>
        {`
          .dot {
            width: 8px;
            height: 8px;
            background: #1a73e8;
            border-radius: 50%;
            animation: pulse 1.4s infinite;
          }

          @keyframes pulse {
            0% { opacity: 0.3; }
            50% { opacity: 1; }
            100% { opacity: 0.3; }
          }
        `}
      </style>
    </div>
  );
}

export default App;
