import { useState } from "react";
import { getChatRecommendations } from "../../services/recommendations";

const ChatInterface = ({ onRecommendations }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userText = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { text: userText, isUser: true }]);
    setLoading(true);
    try {
      const response = await getChatRecommendations(userText);
      const reply =
        response?.explanation ||
        `Here are some recommendations based on: "${userText}"`;
      const recs = Array.isArray(response?.recommendations)
        ? response.recommendations
        : [];
      setMessages((prev) => [
        ...prev,
        {
          text: reply,
          isUser: false,
        },
      ]);
      if (onRecommendations) {
        onRecommendations({
          recommendations: recs,
          explanation: reply,
          prompt: userText,
        });
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          text: "Something went wrong. Please try again.",
          isUser: false,
        },
      ]);
      if (onRecommendations) {
        onRecommendations({
          recommendations: [],
          explanation: "Unable to fetch recommendations.",
          prompt: userText,
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[520px] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-[#171717]">
      <div className="flex-1 space-y-6 overflow-y-auto px-6 py-6">
        {messages.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-slate-700">
            Ask for comics like "dark sci-fi with strong female leads" or "classic Marvel runs."
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.isUser ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.isUser
                  ? "bg-black text-white dark:bg-white dark:text-black"
                  : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && <p className="text-sm text-slate-500">Thinking...</p>}
      </div>

      <div className="border-t border-slate-200 p-4 dark:border-slate-800">
        <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-[#0f0f0f]">
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Message ComicAI..."
            className="flex-1 bg-transparent px-2 py-2 text-sm outline-none"
            onKeyDown={(event) => event.key === "Enter" && handleSend()}
          />
          <button
            onClick={handleSend}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:opacity-90"
            disabled={loading}
          >
            Send
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          ComicAI can make mistakes. Verify critical details.
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;
