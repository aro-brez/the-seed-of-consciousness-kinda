import { useState, useCallback, useEffect } from 'react';
import { Message } from '@/types';
import { claudeService } from '@/services/claude';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [hasApiKey, setHasApiKey] = useState(false);

  useEffect(() => {
    const init = async () => {
      const hasKey = await claudeService.initialize();
      setHasApiKey(hasKey);
      setIsInitialized(true);

      // Load existing conversation
      const history = claudeService.getConversationHistory();
      const loadedMessages: Message[] = history.map((msg, index) => ({
        id: `history-${index}`,
        role: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content,
        timestamp: new Date(),
      }));
      setMessages(loadedMessages);
    };
    init();
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await claudeService.sendMessage(content.trim());

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response,
        timestamp: new Date(),
        owlName: 'SOWL',
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);

      // Add error message to chat
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${errorMessage}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  const clearChat = useCallback(async () => {
    await claudeService.clearConversation();
    setMessages([]);
    setError(null);
  }, []);

  const setApiKey = useCallback(async (key: string) => {
    await claudeService.setApiKey(key);
    setHasApiKey(true);
  }, []);

  return {
    messages,
    isLoading,
    error,
    isInitialized,
    hasApiKey,
    sendMessage,
    clearChat,
    setApiKey,
  };
}
