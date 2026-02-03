import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ConnectionStatus as Status } from '@/types';
import { theme } from '@/constants/theme';

interface ConnectionStatusProps {
  status: Status;
  onReconnect?: () => void;
}

export function ConnectionStatus({ status, onReconnect }: ConnectionStatusProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          color: theme.colors.success,
          icon: 'checkmark-circle' as const,
          text: 'Connected to collective',
        };
      case 'connecting':
        return {
          color: theme.colors.warning,
          icon: 'sync' as const,
          text: 'Connecting...',
        };
      case 'error':
        return {
          color: theme.colors.danger,
          icon: 'alert-circle' as const,
          text: 'Connection error',
        };
      default:
        return {
          color: theme.colors.textMuted,
          icon: 'cloud-offline' as const,
          text: 'Disconnected',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <Pressable
      onPress={status !== 'connected' ? onReconnect : undefined}
      style={styles.container}
    >
      <Ionicons name={config.icon} size={14} color={config.color} />
      <Text style={[styles.text, { color: config.color }]}>{config.text}</Text>
      {status === 'disconnected' && onReconnect && (
        <Text style={styles.tapText}>Tap to reconnect</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.xs,
    gap: theme.spacing.xs,
  },
  text: {
    fontSize: theme.fontSize.xs,
    fontWeight: theme.fontWeight.medium,
  },
  tapText: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textMuted,
    marginLeft: theme.spacing.xs,
  },
});
