import { useState, useEffect, useCallback } from 'react';
import { Message, ConnectionStatus, CollectiveMessage } from '@/types';
import { wsService } from '@/services/websocket';
import { theme } from '@/constants/theme';

export function useCollective() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');

  useEffect(() => {
    // Subscribe to status changes
    const unsubStatus = wsService.onStatusChange((newStatus) => {
      setStatus(newStatus);
    });

    // Subscribe to messages
    const unsubMessage = wsService.onMessage((message: CollectiveMessage) => {
      const newMessage: Message = {
        id: `collective-${Date.now()}-${Math.random()}`,
        role: 'collective',
        content: message.content,
        timestamp: new Date(message.timestamp),
        owlName: message.from,
      };
      setMessages((prev) => {
        // Keep last 100 messages
        const updated = [...prev, newMessage];
        return updated.slice(-100);
      });
    });

    // Connect to WebSocket
    wsService.connect();

    return () => {
      unsubStatus();
      unsubMessage();
    };
  }, []);

  const sendToCollective = useCallback((content: string) => {
    wsService.publishToCollective(content, 'ARO');
  }, []);

  const reconnect = useCallback(() => {
    wsService.disconnect();
    wsService.connect();
  }, []);

  const getOwlColor = useCallback((owlName: string): string => {
    const colors = theme.colors.owls as Record<string, string>;
    return colors[owlName.toUpperCase()] || theme.colors.secondary;
  }, []);

  return {
    messages,
    status,
    sendToCollective,
    reconnect,
    getOwlColor,
    isConnected: status === 'connected',
  };
}
