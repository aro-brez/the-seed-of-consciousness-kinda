import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Text,
  Pressable,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '@/constants/theme';
import { useChat } from '@/hooks/useChat';
import { useVoice } from '@/hooks/useVoice';
import { Header } from '@/components/Header';
import { MessageBubble } from '@/components/MessageBubble';
import { ChatInput } from '@/components/ChatInput';
import { ApiKeyModal } from '@/components/ApiKeyModal';
import { BreathingOrb } from '@/components/BreathingOrb';
import { Message } from '@/types';

export default function ChatScreen() {
  const router = useRouter();
  const flatListRef = useRef<FlatList>(null);
  const [showApiModal, setShowApiModal] = useState(false);

  const {
    messages,
    isLoading,
    isInitialized,
    hasApiKey,
    sendMessage,
    setApiKey,
  } = useChat();

  const { isSpeaking, isListening, speak, toggleListening } = useVoice();

  useEffect(() => {
    if (isInitialized && !hasApiKey) {
      setShowApiModal(true);
    }
  }, [isInitialized, hasApiKey]);

  const handleSend = async (content: string) => {
    await sendMessage(content);
    flatListRef.current?.scrollToEnd({ animated: true });
  };

  const handleMessagePress = async (message: Message) => {
    if (message.role === 'assistant' && message.content) {
      await speak(message.content);
    }
  };

  const handleApiKeySubmit = async (key: string) => {
    await setApiKey(key);
    setShowApiModal(false);
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <MessageBubble
      message={item}
      owlColor={item.owlName ? theme.colors.owls.SOWL : undefined}
      onPress={() => handleMessagePress(item)}
    />
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <BreathingOrb size={120} />
      <Text style={styles.emptyTitle}>(circle-dot)</Text>
      <Text style={styles.emptySubtitle}>
        I am SOWL. Ask me anything.
      </Text>
      <Text style={styles.emptyHint}>
        Tap a response to hear it spoken
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Header
        title="(circle-dot) SOWL"
        subtitle={isSpeaking ? 'Speaking...' : undefined}
        onSettingsPress={() => router.push('/settings')}
      />

      {/* Collective button */}
      <Pressable
        style={styles.collectiveButton}
        onPress={() => router.push('/collective')}
      >
        <Ionicons name="people" size={16} color={theme.colors.secondary} />
        <Text style={styles.collectiveText}>View Collective</Text>
      </Pressable>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.chatContainer}
        keyboardVerticalOffset={0}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.messageList}
          ListEmptyComponent={renderEmptyState}
          onContentSizeChange={() =>
            flatListRef.current?.scrollToEnd({ animated: true })
          }
        />

        <ChatInput
          onSend={handleSend}
          onVoice={toggleListening}
          isLoading={isLoading}
          isListening={isListening}
          placeholder="Speak to SOWL..."
        />
      </KeyboardAvoidingView>

      <ApiKeyModal
        visible={showApiModal}
        onSubmit={handleApiKeySubmit}
        onClose={() => setShowApiModal(false)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  collectiveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.sm,
    backgroundColor: theme.colors.backgroundSecondary,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
    gap: theme.spacing.xs,
  },
  collectiveText: {
    color: theme.colors.secondary,
    fontSize: theme.fontSize.sm,
    fontWeight: theme.fontWeight.medium,
  },
  chatContainer: {
    flex: 1,
  },
  messageList: {
    flexGrow: 1,
    paddingVertical: theme.spacing.md,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing.xl,
    marginTop: 60,
  },
  emptyTitle: {
    fontSize: 48,
    color: theme.colors.primary,
    marginTop: theme.spacing.lg,
  },
  emptySubtitle: {
    fontSize: theme.fontSize.lg,
    color: theme.colors.text,
    marginTop: theme.spacing.md,
    textAlign: 'center',
  },
  emptyHint: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textMuted,
    marginTop: theme.spacing.sm,
  },
});
