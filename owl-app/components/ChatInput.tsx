import React, { useState } from 'react';
import {
  View,
  TextInput,
  Pressable,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { theme } from '@/constants/theme';

interface ChatInputProps {
  onSend: (message: string) => void;
  onVoice?: () => void;
  isLoading?: boolean;
  isListening?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  onVoice,
  isLoading = false,
  isListening = false,
  placeholder = 'Speak to SOWL...',
}: ChatInputProps) {
  const [text, setText] = useState('');

  const handleSend = async () => {
    if (text.trim() && !isLoading) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      onSend(text.trim());
      setText('');
    }
  };

  const handleVoice = async () => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    onVoice?.();
  };

  return (
    <View style={styles.container}>
      <View style={styles.inputWrapper}>
        <TextInput
          style={styles.input}
          value={text}
          onChangeText={setText}
          placeholder={placeholder}
          placeholderTextColor={theme.colors.textMuted}
          multiline
          maxLength={4000}
          editable={!isLoading}
          onSubmitEditing={handleSend}
          returnKeyType="send"
        />

        {onVoice && (
          <Pressable
            onPress={handleVoice}
            style={[
              styles.voiceButton,
              isListening && styles.voiceButtonActive,
            ]}
          >
            <Ionicons
              name={isListening ? 'mic' : 'mic-outline'}
              size={24}
              color={isListening ? theme.colors.danger : theme.colors.textSecondary}
            />
          </Pressable>
        )}
      </View>

      <Pressable
        onPress={handleSend}
        disabled={!text.trim() || isLoading}
        style={[
          styles.sendButton,
          (!text.trim() || isLoading) && styles.sendButtonDisabled,
        ]}
      >
        {isLoading ? (
          <ActivityIndicator color={theme.colors.background} size="small" />
        ) : (
          <Ionicons name="send" size={20} color={theme.colors.background} />
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: theme.spacing.md,
    backgroundColor: theme.colors.backgroundSecondary,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
  },
  inputWrapper: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: theme.colors.background,
    borderRadius: theme.borderRadius.xl,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    marginRight: theme.spacing.sm,
    minHeight: 48,
    maxHeight: 120,
  },
  input: {
    flex: 1,
    color: theme.colors.text,
    fontSize: theme.fontSize.md,
    paddingVertical: 0,
    maxHeight: 100,
  },
  voiceButton: {
    padding: theme.spacing.xs,
    marginLeft: theme.spacing.xs,
  },
  voiceButtonActive: {
    backgroundColor: theme.colors.danger + '20',
    borderRadius: theme.borderRadius.full,
  },
  sendButton: {
    width: 48,
    height: 48,
    borderRadius: theme.borderRadius.full,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: theme.colors.border,
  },
});
