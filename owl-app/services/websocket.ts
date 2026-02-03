import { config } from '@/constants/config';
import { WSMessage, CollectiveMessage, ConnectionStatus } from '@/types';

type MessageHandler = (message: CollectiveMessage) => void;
type StatusHandler = (status: ConnectionStatus) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();
  private statusHandlers: Set<StatusHandler> = new Set();
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private isIntentionalClose = false;
  private currentStatus: ConnectionStatus = 'disconnected';

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.isIntentionalClose = false;
    this.updateStatus('connecting');

    try {
      this.ws = new WebSocket(config.natsWebSocketUrl);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.updateStatus('connected');

        // Subscribe to collective messages
        this.send({
          action: 'subscribe',
          subject: 'owl.all',
        });

        // Also subscribe to collective channel
        this.send({
          action: 'subscribe',
          subject: 'owl.collective',
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const message = this.parseMessage(data);
          if (message) {
            this.notifyMessageHandlers(message);
          }
        } catch (error) {
          // Try to handle as plain text
          if (event.data && typeof event.data === 'string' && event.data.length > 2) {
            const message: CollectiveMessage = {
              from: 'COLLECTIVE',
              type: 'message',
              content: event.data,
              timestamp: new Date().toISOString(),
            };
            this.notifyMessageHandlers(message);
          }
        }
      };

      this.ws.onerror = () => {
        this.updateStatus('error');
      };

      this.ws.onclose = () => {
        this.updateStatus('disconnected');
        if (!this.isIntentionalClose) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.updateStatus('error');
      this.scheduleReconnect();
    }
  }

  private parseMessage(data: WSMessage): CollectiveMessage | null {
    // Handle different message formats
    if (data.content || data.message) {
      return {
        from: data.from || 'OWL',
        type: data.type || 'message',
        content: data.content || data.message || '',
        timestamp: data.timestamp || new Date().toISOString(),
      };
    }

    // Try to parse nested data
    if (data.data) {
      try {
        const nested = typeof data.data === 'string' ? JSON.parse(data.data) : data.data;
        if (nested.content || nested.message) {
          return {
            from: nested.from || 'OWL',
            type: nested.type || 'message',
            content: nested.content || nested.message || '',
            timestamp: nested.timestamp || new Date().toISOString(),
          };
        }
      } catch {
        // Not JSON, use as-is
        return {
          from: 'OWL',
          type: 'message',
          content: String(data.data),
          timestamp: new Date().toISOString(),
        };
      }
    }

    return null;
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    if (this.reconnectAttempts < config.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(
        config.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1),
        30000
      );

      this.reconnectTimeout = setTimeout(() => {
        this.connect();
      }, delay);
    }
  }

  disconnect(): void {
    this.isIntentionalClose = true;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.updateStatus('disconnected');
  }

  send(message: WSMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  publishToCollective(content: string, from: string = 'ARO'): void {
    const payload: CollectiveMessage = {
      from,
      type: 'message',
      content,
      timestamp: new Date().toISOString(),
    };

    this.send({
      action: 'publish',
      subject: 'owl.all',
      data: JSON.stringify(payload),
    });
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => {
      this.messageHandlers.delete(handler);
    };
  }

  onStatusChange(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    // Immediately notify of current status
    handler(this.currentStatus);
    return () => {
      this.statusHandlers.delete(handler);
    };
  }

  private notifyMessageHandlers(message: CollectiveMessage): void {
    this.messageHandlers.forEach((handler) => {
      try {
        handler(message);
      } catch (error) {
        console.error('Message handler error:', error);
      }
    });
  }

  private updateStatus(status: ConnectionStatus): void {
    this.currentStatus = status;
    this.statusHandlers.forEach((handler) => {
      try {
        handler(status);
      } catch (error) {
        console.error('Status handler error:', error);
      }
    });
  }

  getStatus(): ConnectionStatus {
    return this.currentStatus;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsService = new WebSocketService();
