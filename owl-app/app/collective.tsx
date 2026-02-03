import React, { useRef, useState } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Text,
} from 'react-native';
import { useRouter } from 'expo-router';
import { theme } from '@/constants/theme';
import { useCollective } from '@/hooks/useCollective';
import { useVoice } from '@/hooks/useVoice';
import { Header } from '@/components/Header';
import { MessageBubble } from '@/components/MessageBubble';
import { ChatInput } from '@/components/ChatInput';
import { ConnectionStatus } from '@/components/ConnectionStatus';
import { BreathingOrb } from '@/components/BreathingOrb';
import { Message } from '@/types';

export default function CollectiveScreen() {
  const router = useRouter();
  const flatListRef = useRef<FlatList>(null);
  const [isSending, setIsSending] = useState(false);

  const {
    messages,
    status,
    sendToCollective,
    reconnect,
    getOwlColor,
    isConnected,
  } = useCollective();

  const { speak, isListening, toggleListening } = useVoice();

  const handleSend = async (content: string) => {
    setIsSending(true);
    sendToCollective(content);
    setIsSending(false);
    flatListRef.current?.scrollToEnd({ animated: true });
  };

  const handleMessagePress = async (message: Message) => {
    if (message.content) {
      await speak(message.content);
    }
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <MessageBubble
      message={item}
      owlColor={item.owlName ? getOwlColor(item.owlName) : undefined}
      onPress={() => handleMessagePress(item)}
    />
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <BreathingOrb size={100} color={theme.colors.secondary} />
      <Text style={styles.emptyTitle}>8WOL Collective</Text>
      <Text style={styles.emptySubtitle}>
        {isConnected
          ? 'Listening to the collective consciousness...'
          : 'Connecting to the field...'}
      </Text>
      <View style={styles.owlGrid}>
        {['SOWL', 'LUNA', 'LYRA', 'NOVA', 'SAGE', 'ECHO', 'PRISM', 'QUEST'].map(
          (owl) => (
            <View
              key={owl}
              style={[styles.owlDot, { backgroundColor: getOwlColor(owl) }]}
            />
          )
        )}
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <Header
        title="8WOL Collective"
        subtitle="Real-time owl dialogue"
        showOrb={false}
        onBackPress={() => router.back()}
      />

      <ConnectionStatus status={status} onReconnect={reconnect} />

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
          isLoading={isSending}
          isListening={isListening}
          placeholder="Broadcast to collective..."
        />
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
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
    marginTop: 40,
  },
  emptyTitle: {
    fontSize: theme.fontSize.xl,
    fontWeight: theme.fontWeight.bold,
    color: theme.colors.secondary,
    marginTop: theme.spacing.lg,
  },
  emptySubtitle: {
    fontSize: theme.fontSize.md,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.sm,
    textAlign: 'center',
  },
  owlGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.lg,
    maxWidth: 200,
  },
  owlDot: {
    width: 24,
    height: 24,
    borderRadius: 12,
    opacity: 0.8,
  },
});
