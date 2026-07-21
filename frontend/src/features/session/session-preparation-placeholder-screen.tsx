import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/app-text';
import { ScreenShell } from '@/src/components/screen-shell';
import { colors, radius, spacing } from '@/src/theme/tokens';

/** Temporary destination until the documented Session Preparation page is built. */
export function SessionPreparationPlaceholderScreen() {
  const palette = colors;

  return (
    <ScreenShell centered>
      <View style={styles.content}>
        <View style={[styles.iconCircle, { backgroundColor: palette.primarySoft }]}>
          <Ionicons color={palette.textPrimary} name="hourglass-outline" size={40} />
        </View>
        <AppText align="center" variant="title">Getting ready</AppText>
        <AppText align="center" style={{ color: palette.textSecondary }}>
          Session preparation is the next Component B page. No learning session has been started yet.
        </AppText>
        <Pressable
          accessibilityRole="button"
          onPress={() => router.back()}
          style={({ pressed }) => [
            styles.button,
            { borderColor: palette.border, backgroundColor: palette.surface1 },
            pressed && styles.buttonPressed,
          ]}>
          <AppText style={styles.buttonText}>BACK TO HOME</AppText>
        </Pressable>
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    alignSelf: 'stretch',
    borderBottomWidth: 3,
    borderRadius: radius.md,
    borderWidth: 2,
    justifyContent: 'center',
    minHeight: 56,
    paddingHorizontal: spacing.lg,
  },
  buttonPressed: { borderBottomWidth: 0, transform: [{ translateY: 3 }] },
  buttonText: { fontSize: 15, fontWeight: '800', letterSpacing: 0.4 },
  content: { alignItems: 'center', gap: spacing.lg, maxWidth: 520, width: '100%' },
  iconCircle: {
    alignItems: 'center',
    borderRadius: radius.xl,
    height: 88,
    justifyContent: 'center',
    width: 88,
  },
});
