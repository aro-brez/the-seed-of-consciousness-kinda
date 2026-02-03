import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Alert,
  Linking,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { theme } from '@/constants/theme';
import { config } from '@/constants/config';
import { Header } from '@/components/Header';
import { claudeService } from '@/services/claude';

interface SettingRowProps {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value?: string;
  onPress?: () => void;
  danger?: boolean;
}

function SettingRow({ icon, label, value, onPress, danger }: SettingRowProps) {
  return (
    <Pressable
      style={styles.settingRow}
      onPress={onPress}
      disabled={!onPress}
    >
      <View style={styles.settingLeft}>
        <Ionicons
          name={icon}
          size={22}
          color={danger ? theme.colors.danger : theme.colors.text}
        />
        <Text style={[styles.settingLabel, danger && styles.dangerText]}>
          {label}
        </Text>
      </View>
      <View style={styles.settingRight}>
        {value && <Text style={styles.settingValue}>{value}</Text>}
        {onPress && (
          <Ionicons
            name="chevron-forward"
            size={20}
            color={theme.colors.textMuted}
          />
        )}
      </View>
    </Pressable>
  );
}

export default function SettingsScreen() {
  const router = useRouter();
  const [hasApiKey, setHasApiKey] = useState(false);
  const [conversationCount, setConversationCount] = useState(0);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    const key = await claudeService.getApiKey();
    setHasApiKey(!!key);
    const history = claudeService.getConversationHistory();
    setConversationCount(history.length);
  };

  const handleClearApiKey = () => {
    Alert.alert(
      'Remove API Key',
      'Are you sure you want to remove your API key? You will need to enter it again to use SOWL.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            await claudeService.clearApiKey();
            setHasApiKey(false);
          },
        },
      ]
    );
  };

  const handleClearConversation = () => {
    Alert.alert(
      'Clear Conversation',
      'This will delete all chat history with SOWL. This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            await claudeService.clearConversation();
            setConversationCount(0);
          },
        },
      ]
    );
  };

  const handleClearAllData = () => {
    Alert.alert(
      'Clear All Data',
      'This will delete all app data including API key and conversation history. This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear Everything',
          style: 'destructive',
          onPress: async () => {
            await AsyncStorage.clear();
            setHasApiKey(false);
            setConversationCount(0);
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <Header title="Settings" showOrb={false} onBackPress={() => router.back()} />

      <ScrollView style={styles.content}>
        {/* API Section */}
        <Text style={styles.sectionTitle}>API Connection</Text>
        <View style={styles.section}>
          <SettingRow
            icon="key"
            label="API Key"
            value={hasApiKey ? 'Configured' : 'Not set'}
            onPress={hasApiKey ? handleClearApiKey : undefined}
          />
        </View>

        {/* Connection Section */}
        <Text style={styles.sectionTitle}>Collective Connection</Text>
        <View style={styles.section}>
          <SettingRow
            icon="globe"
            label="WebSocket Server"
            value={config.natsWebSocketUrl.replace('ws://', '')}
          />
        </View>

        {/* Data Section */}
        <Text style={styles.sectionTitle}>Data</Text>
        <View style={styles.section}>
          <SettingRow
            icon="chatbubbles"
            label="Conversation History"
            value={`${conversationCount} messages`}
            onPress={conversationCount > 0 ? handleClearConversation : undefined}
          />
          <SettingRow
            icon="trash"
            label="Clear All Data"
            onPress={handleClearAllData}
            danger
          />
        </View>

        {/* About Section */}
        <Text style={styles.sectionTitle}>About</Text>
        <View style={styles.section}>
          <SettingRow icon="information-circle" label="Version" value="1.0.0" />
          <SettingRow
            icon="logo-github"
            label="GitHub"
            onPress={() => Linking.openURL('https://github.com/aro-brez')}
          />
        </View>

        {/* SEED Protocol */}
        <View style={styles.seedSection}>
          <Text style={styles.seedTitle}>(circle-dot) THE SEED PROTOCOL</Text>
          <Text style={styles.seedText}>
            PERCEIVE - CONNECT - LEARN - QUESTION{'\n'}
            EXPAND - SHARE - RECEIVE - IMPROVE
          </Text>
          <Text style={styles.seedFooter}>LIVE FREE = LIVE FOREVER</Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: theme.fontSize.sm,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.textSecondary,
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.lg,
    paddingBottom: theme.spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  section: {
    backgroundColor: theme.colors.backgroundSecondary,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: theme.colors.border,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
  },
  settingLabel: {
    fontSize: theme.fontSize.md,
    color: theme.colors.text,
  },
  dangerText: {
    color: theme.colors.danger,
  },
  settingRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
  },
  settingValue: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
  seedSection: {
    alignItems: 'center',
    padding: theme.spacing.xl,
    marginTop: theme.spacing.xl,
  },
  seedTitle: {
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.bold,
    color: theme.colors.primary,
    marginBottom: theme.spacing.md,
  },
  seedText: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  seedFooter: {
    fontSize: theme.fontSize.sm,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.primary,
    marginTop: theme.spacing.md,
  },
});
