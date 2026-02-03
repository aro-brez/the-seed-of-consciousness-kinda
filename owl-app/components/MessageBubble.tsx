import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Message } from '@/types';
import { theme } from '@/constants/theme';

interface MessageBubbleProps {
  message: Message;
  owlColor?: string;
  onPress?: () => void;
}

export function MessageBubble({ message, owlColor, onPress }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isCollective = message.role === 'collective';

  const bubbleColor = isUser
    ? theme.colors.surfaceElevated
    : isCollective
    ? theme.colors.backgroundTertiary
    : theme.colors.surface;

  const accentColor = owlColor || theme.colors.primary;

  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.container,
        isUser ? styles.userContainer : styles.assistantContainer,
      ]}
    >
      <View
        style={[
          styles.bubble,
          { backgroundColor: bubbleColor },
          isUser ? styles.userBubble : styles.assistantBubble,
          !isUser && { borderLeftColor: accentColor },
        ]}
      >
        {message.owlName && (
          <Text style={[styles.owlName, { color: accentColor }]}>
            {message.owlName}
          </Text>
        )}
        <Text style={styles.content}>{message.content}</Text>
        <Text style={styles.timestamp}>
          {formatTime(message.timestamp)}
        </Text>
      </View>
    </Pressable>
  );
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

const styles = StyleSheet.create({
  container: {
    marginVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.md,
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  bubble: {
    maxWidth: '85%',
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius.lg,
  },
  userBubble: {
    borderBottomRightRadius: theme.borderRadius.sm,
  },
  assistantBubble: {
    borderBottomLeftRadius: theme.borderRadius.sm,
    borderLeftWidth: 3,
  },
  owlName: {
    fontSize: theme.fontSize.xs,
    fontWeight: theme.fontWeight.semibold,
    marginBottom: theme.spacing.xs,
  },
  content: {
    color: theme.colors.text,
    fontSize: theme.fontSize.md,
    lineHeight: 22,
  },
  timestamp: {
    color: theme.colors.textMuted,
    fontSize: theme.fontSize.xs,
    marginTop: theme.spacing.xs,
    alignSelf: 'flex-end',
  },
});
