import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import api from "../lib/api";

export type MessageRole = "user" | "bot";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  status: "pending" | "sent" | "error";
  createdAt: number;
}

interface ApiMessage {
  id: number | string;
  role: MessageRole | "system";
  content: string;
  response_text?: string;
  created_at: string;
}

interface ApiSession {
  id: number | string;
  user_id: string;
  messages: ApiMessage[];
}

interface UseChatResult {
  messages: ChatMessage[];
  isTyping: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  resetConversation: () => void;
}

const STORAGE_PREFIX = "shoshchat.widget.history";

const generateId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const buildStorageKey = (tenantId: string) => `${STORAGE_PREFIX}.${tenantId}`;

const loadStoredMessages = (tenantId: string): ChatMessage[] => {
  if (typeof window === "undefined") {
    return [];
  }
  try {
    const stored = window.localStorage.getItem(buildStorageKey(tenantId));
    if (!stored) return [];
    const parsed = JSON.parse(stored) as ChatMessage[];
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    console.warn("Unable to load cached messages", error);
    return [];
  }
};

const persistMessages = (tenantId: string, messages: ChatMessage[]) => {
  if (typeof window === "undefined") {
    return;
  }
  try {
    const snapshot = messages.slice(-50);
    window.localStorage.setItem(buildStorageKey(tenantId), JSON.stringify(snapshot));
  } catch (error) {
    console.warn("Unable to persist chat history", error);
  }
};

const useChat = (tenantId: string): UseChatResult => {
  const initialMessages = useMemo(() => loadStoredMessages(tenantId), [tenantId]);
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasMountedRef = useRef(false);
  const historyFetchedFor = useRef<string | null>(null);

  useEffect(() => {
    if (hasMountedRef.current) {
      persistMessages(tenantId, messages);
    } else {
      hasMountedRef.current = true;
    }
  }, [messages, tenantId]);

  useEffect(() => {
    setMessages(loadStoredMessages(tenantId));
    setError(null);
    setIsTyping(false);
    historyFetchedFor.current = null;
  }, [tenantId]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    if (historyFetchedFor.current === tenantId) {
      return;
    }
    const token = window.localStorage.getItem("shoshchat.token");
    if (!token) {
      return;
    }

    let isActive = true;

    const hydrateMessages = (session: ApiSession | undefined) => {
      if (!session) return [];
      const collected: ChatMessage[] = [];
      session.messages
        .slice()
        .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
        .forEach((message) => {
          const createdAt = new Date(message.created_at).getTime();
          const role: MessageRole = message.role === "user" ? "user" : "bot";
          collected.push({
            id: `remote-${session.id}-${message.id}-prompt`,
            role,
            content: message.content,
            status: "sent",
            createdAt,
          });
          if (message.response_text) {
            collected.push({
              id: `remote-${session.id}-${message.id}-reply`,
              role: "bot",
              content: message.response_text,
              status: "sent",
              createdAt: createdAt + 1,
            });
          }
        });
      return collected;
    };

    const fetchHistory = async () => {
      let shouldMarkFetched = true;
      try {
        const response = await api.get<ApiSession[]>("/chat/sessions/");
        if (!isActive) return;
        const sessions = response.data ?? [];
        const session = sessions.find((item) => item.user_id === `widget-${tenantId}`);
        if (!session) {
          historyFetchedFor.current = tenantId;
          return;
        }
        const hydrated = hydrateMessages(session);
        if (hydrated.length === 0) {
          historyFetchedFor.current = tenantId;
          return;
        }
        setMessages((current) => (current.length > 0 ? current : hydrated));
      } catch (fetchError) {
        const status = (fetchError as { response?: { status?: number } })?.response?.status;
        if (status === 401) {
          shouldMarkFetched = false;
        } else {
          console.warn("Unable to load remote chat history", fetchError);
        }
      } finally {
        if (shouldMarkFetched) {
          historyFetchedFor.current = tenantId;
        }
      }
    };

    void fetchHistory();

    return () => {
      isActive = false;
    };
  }, [tenantId]);

  const sendMessage = useCallback(
    async (rawContent: string) => {
      const content = rawContent.trim();
      if (!content) {
        return;
      }
      if (isTyping) {
        return;
      }

      setError(null);
      const userMessage: ChatMessage = {
        id: generateId(),
        role: "user",
        content,
        status: "sent",
        createdAt: Date.now(),
      };
      const pendingReplyId = generateId();
      const pendingMessage: ChatMessage = {
        id: pendingReplyId,
        role: "bot",
        content: "…",
        status: "pending",
        createdAt: Date.now(),
      };

      setMessages((prev) => [...prev, userMessage, pendingMessage]);
      setIsTyping(true);

      try {
        const response = await api.post("/chat/", {
          message: content,
          user_id: `widget-${tenantId}`,
        });
        const reply = response.data?.reply ?? "No response available.";
        setMessages((prev) =>
          prev.map((message) =>
            message.id === pendingReplyId
              ? {
                  ...message,
                  status: "sent",
                  content: reply,
                  createdAt: Date.now(),
                }
              : message
          )
        );
      } catch (requestError) {
        console.error(requestError);
        setError("We ran into a connectivity issue. Please try again.");
        setMessages((prev) =>
          prev.map((message) =>
            message.id === pendingReplyId
              ? {
                  ...message,
                  status: "error",
                  content: "Unable to reach ShoshChat right now.",
                }
              : message
          )
        );
      } finally {
        setIsTyping(false);
      }
    },
    [isTyping, tenantId]
  );

  const resetConversation = useCallback(() => {
    setMessages([]);
    setError(null);
    setIsTyping(false);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(buildStorageKey(tenantId));
    }
  }, [tenantId]);

  return {
    messages,
    isTyping,
    error,
    sendMessage,
    resetConversation,
  };
};

export default useChat;
