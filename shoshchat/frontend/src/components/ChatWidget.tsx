import { useEffect, useRef, useState } from "react";
import useChat from "../hooks/useChat";

interface ChatWidgetProps {
  tenantId: string;
  accent?: "retail" | "finance";
}

const ChatWidget = ({ tenantId }: ChatWidgetProps) => {
  const { messages, sendMessage, isTyping, error, resetConversation } = useChat(tenantId);
  const [isOpen, setIsOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const hasPendingMessage = messages.some((message) => message.status === "pending");

  if (!isOpen) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setIsOpen(true)}
          className="group w-[60px] h-[60px] rounded-full shadow-lg bg-[#2563eb] hover:bg-[#1d4ed8] transition-all duration-300 flex items-center justify-center hover:scale-105"
          style={{ fontFamily: "'Open Sans', sans-serif" }}
        >
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50" style={{ fontFamily: "'Open Sans', sans-serif" }}>
      <div className="w-[380px] h-[580px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-5 bg-[#2563eb] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-[10px] bg-white flex items-center justify-center">
              <span className="text-xl">💬</span>
            </div>
            <div>
              <h3 className="text-white font-semibold text-base">Support Chat</h3>
              <div className="flex items-center gap-1.5 text-white/90 text-xs">
                <div className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></div>
                <span>Online</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={resetConversation}
              className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 transition-colors flex items-center justify-center text-white text-xs"
              title="Clear chat"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 transition-colors flex items-center justify-center"
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-[#fafafa]">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="w-12 h-12 mx-auto mb-3 rounded-lg bg-[#e2e8f0] flex items-center justify-center">
                <svg className="w-6 h-6 text-[#64748b]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <p className="text-[#64748b] text-sm">Start a conversation with us!</p>
            </div>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-semibold flex-shrink-0 ${
                msg.role === "user" ? "bg-[#64748b] text-white" : "bg-[#2563eb] text-white"
              }`}>
                {msg.role === "user" ? "U" : "AI"}
              </div>
              <div className="flex flex-col max-w-[75%]">
                <div className={`px-4 py-3 rounded-xl ${
                  msg.role === "user"
                    ? "bg-[#2563eb] text-white"
                    : msg.status === "error"
                    ? "bg-[#fee2e2] border border-[#fecaca] text-[#991b1b]"
                    : "bg-white border border-[#e2e8f0] text-[#1e293b]"
                }`}>
                  {msg.status === "pending" ? (
                    <div className="flex space-x-1">
                      <span className="h-2 w-2 rounded-full bg-[#94a3b8] animate-bounce [animation-delay:-0.1s]"></span>
                      <span className="h-2 w-2 rounded-full bg-[#94a3b8] animate-bounce"></span>
                      <span className="h-2 w-2 rounded-full bg-[#94a3b8] animate-bounce [animation-delay:0.1s]"></span>
                    </div>
                  ) : (
                    <p className="text-sm leading-relaxed">{msg.content}</p>
                  )}
                </div>
                <span className="text-[11px] text-[#94a3b8] mt-1 px-1">
                  {new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))}

          {isTyping && !hasPendingMessage && (
            <div className="flex gap-2.5 flex-row">
              <div className="w-8 h-8 rounded-lg bg-[#2563eb] flex items-center justify-center text-sm font-semibold text-white flex-shrink-0">
                AI
              </div>
              <div className="bg-white border border-[#e2e8f0] px-4 py-3 rounded-xl">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-[#94a3b8] rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-[#94a3b8] rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                  <div className="w-2 h-2 bg-[#94a3b8] rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-5 bg-white border-t border-[#e2e8f0]">
          {error ? (
            <div className="mb-3 rounded-lg border border-[#fecaca] bg-[#fee2e2] px-3 py-2 text-xs text-[#991b1b]">
              Unable to reach ShoshChat right now.
            </div>
          ) : null}
          <form
            className="flex gap-3 items-center"
            onSubmit={(event) => {
              event.preventDefault();
              if (!draft.trim()) return;
              void sendMessage(draft);
              setDraft("");
            }}
          >
            <input
              ref={inputRef}
              type="text"
              placeholder="Type your message..."
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              className="flex-1 px-4 py-3 border border-[#e2e8f0] rounded-[10px] focus:outline-none focus:border-[#2563eb] transition-colors text-sm placeholder:text-[#94a3b8]"
              disabled={isTyping}
            />
            <button
              type="submit"
              className={`w-11 h-11 rounded-[10px] bg-[#2563eb] hover:bg-[#1d4ed8] transition-colors flex items-center justify-center flex-shrink-0 ${
                !draft.trim() || isTyping ? "opacity-50 cursor-not-allowed" : ""
              }`}
              disabled={!draft.trim() || isTyping}
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" />
              </svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatWidget;
