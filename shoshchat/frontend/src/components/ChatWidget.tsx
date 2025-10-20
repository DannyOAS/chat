import { useEffect, useMemo, useRef } from "react";
import useChat from "../hooks/useChat";

interface ChatWidgetProps {
  tenantId: string;
  accent?: "retail" | "finance";
}

const themeStyles = {
  retail: {
    border: "border-retail-accent/30",
    bubble: "bg-retail-primary/20",
    button: "bg-retail-primary text-slate-900",
    ring: "focus:ring-retail-accent/60"
  },
  finance: {
    border: "border-finance-accent/30",
    bubble: "bg-finance-primary/20",
    button: "bg-finance-primary text-white",
    ring: "focus:ring-finance-accent/60"
  }
} as const;

const ChatWidget = ({ tenantId, accent = "retail" }: ChatWidgetProps) => {
  const { messages, sendMessage } = useChat(tenantId);
  const inputRef = useRef<HTMLInputElement>(null);
  const styles = useMemo(() => themeStyles[accent], [accent]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <div className={`max-w-sm w-full rounded-xl shadow-xl bg-slate-800 border ${styles.border}`}>
      <div className="p-4 border-b border-slate-700 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">ShoshChat AI</h2>
          <p className="text-xs text-slate-400">Tenant: {tenantId}</p>
        </div>
      </div>
      <div className="h-64 overflow-y-auto space-y-3 p-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`rounded-lg px-3 py-2 text-sm ${msg.role === "bot" ? "bg-slate-700" : styles.bubble}`}
          >
            {msg.content}
          </div>
        ))}
      </div>
      <form
        className="flex gap-2 border-t border-slate-700 p-3"
        onSubmit={(event) => {
          event.preventDefault();
          if (!inputRef.current?.value) return;
          sendMessage(inputRef.current.value);
          inputRef.current.value = "";
        }}
      >
        <input
          ref={inputRef}
          type="text"
          placeholder="Ask something..."
          className={`flex-1 rounded-md bg-slate-900 border border-slate-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 ${styles.ring}`}
        />
        <button
          type="submit"
          className={`rounded-md px-3 py-2 text-sm font-medium ${styles.button}`}
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatWidget;
