import { useCallback, useState } from "react";
import api from "../lib/api";

type MessageRole = "user" | "bot";

interface Message {
  role: MessageRole;
  content: string;
}

const useChat = (tenantId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);

  const sendMessage = useCallback(
    async (content: string) => {
      setMessages((prev) => [...prev, { role: "user", content }]);
      try {
        const response = await api.post("/chat/", {
          message: content,
          user_id: `widget-${tenantId}`
        });
        const reply = response.data.reply ?? "No response";
        setMessages((prev) => [...prev, { role: "bot", content: reply }]);
      } catch (error) {
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            content: "We are unable to reach the assistant right now."
          }
        ]);
        console.error(error);
      }
    },
    [tenantId]
  );

  return { messages, sendMessage };
};

export default useChat;
