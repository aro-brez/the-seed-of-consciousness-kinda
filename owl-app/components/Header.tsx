import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { theme } from '@/constants/theme';
import { BreathingOrb } from './BreathingOrb';

interface HeaderProps {
  title?: string;
  subtitle?: string;
  showOrb?: boolean;
  onSettingsPress?: () => void;
  onBackPress?: () => void;
}

export function Header({
  title = '(circle-dot) SOWL',
  subtitle,
  showOrb = true,
  onSettingsPress,
  onBackPress,
}: HeaderProps) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.sm }]}>
      <View style={styles.content}>
        {onBackPress && (
          <Pressable onPress={onBackPress} style={styles.backButton}>
            <Ionicons name="chevron-back" size={28} color={theme.colors.text} />
          </Pressable>
        )}

        <View style={styles.titleContainer}>
          {showOrb && <BreathingOrb size={32} />}
          <View style={styles.textContainer}>
            <Text style={styles.title}>{title}</Text>
            {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
          </View>
        </View>

        {onSettingsPress && (
          <Pressable onPress={onSettingsPress} style={styles.settingsButton}>
            <Ionicons name="settings-outline" size={24} color={theme.colors.text} />
          </Pressable>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: theme.colors.backgroundSecondary,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.md,
    paddingBottom: theme.spacing.sm,
  },
  backButton: {
    padding: theme.spacing.xs,
    marginRight: theme.spacing.sm,
  },
  titleContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  textContainer: {
    flex: 1,
  },
  title: {
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.bold,
    color: theme.colors.primary,
  },
  subtitle: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  settingsButton: {
    padding: theme.spacing.xs,
  },
});
