import { Image } from 'expo-image';
import { router } from 'expo-router';
import { Pressable, StyleSheet, useWindowDimensions, View } from 'react-native';

import {
  LEARNER_TAB_BAR_HEIGHT,
  LEARNER_TAB_BAR_HEIGHT_COMPACT,
  LEARNER_TAB_BAR_MARGIN_BOTTOM,
} from '@/src/features/navigation/chrome-metrics';
import { artwork } from '@/src/utils/artwork';
import { useAdventureCharge } from '@/src/features/navigation/adventure-charge-context';
import { colors, radius, spacing } from '@/src/theme/tokens';

const tabArtwork = {
  play: artwork.tabGame,
  playSelected: artwork.tabGameSelected,
  home: artwork.tabHome,
  homeSelected: artwork.tabHomeSelected,
  profile: artwork.tabProfile,
  profileSelected: artwork.tabProfileSelected,
};

// Re-exported; the values live in chrome-metrics.ts. See that file.
export {
  LEARNER_TAB_BAR_HEIGHT,
  LEARNER_TAB_BAR_HEIGHT_COMPACT,
  LEARNER_TAB_BAR_MARGIN_BOTTOM,
};

type LearnerTab = 'home' | 'play' | 'profile';

export function LearnerTabBar({
  activeTab,
  activeHomePressEnabled = false,
  playEnabled = false,
}: {
  activeTab: LearnerTab;
  activeHomePressEnabled?: boolean;
  playEnabled?: boolean;
}) {
  const compact = useWindowDimensions().height < 760;
  const { requestPlay } = useAdventureCharge();

  return (
    <View style={styles.dock}>
      <View style={[styles.bottomNav, compact && styles.bottomNavCompact]}>
        <TabItem
          active={activeTab === 'play'}
          accessibilityHint={playEnabled ? 'Opens adaptive games' : 'Adaptive games will be available with Component C'}
          disabled={!playEnabled}
          label="Play"
          onPress={requestPlay}
          selectedSource={tabArtwork.playSelected}
          source={tabArtwork.play}
        />
        <TabItem
          active={activeTab === 'home'}
          label="Home"
          onPress={() => router.replace('/(learner)/home')}
          pressWhenActive={activeHomePressEnabled}
          selectedSource={tabArtwork.homeSelected}
          source={tabArtwork.home}
        />
        <TabItem
          active={activeTab === 'profile'}
          label="Profile"
          onPress={() => router.replace('/(learner)/profile')}
          selectedSource={tabArtwork.profileSelected}
          source={tabArtwork.profile}
        />
      </View>
    </View>
  );
}

function TabItem({ active, accessibilityHint, disabled = false, label, onPress, pressWhenActive = false, selectedSource, source }: {
  active: boolean;
  accessibilityHint?: string;
  disabled?: boolean;
  label: string;
  onPress: () => void;
  pressWhenActive?: boolean;
  selectedSource: number;
  source: number;
}) {
  return (
    <Pressable
      accessibilityHint={accessibilityHint}
      accessibilityLabel={`${label} tab${active ? ', selected' : disabled ? ', unavailable' : ''}`}
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || undefined, selected: active }}
      disabled={(active && !pressWhenActive) || disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.navItem,
        active && styles.navItemSelected,
        disabled && styles.navItemDisabled,
        pressed && styles.navItemPressed,
      ]}>
      <Image
        accessible={false}
        contentFit="cover"
        source={active ? selectedSource : source}
        style={styles.navArtwork}
      />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  bottomNav: {
    alignItems: 'center',
    backgroundColor: colors.surface1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderWidth: 1,
    elevation: 6,
    flexDirection: 'row',
    height: 73,
    justifyContent: 'space-around',
    marginBottom: 11.75,
    marginHorizontal: spacing.sm,
    minHeight: 0,
    paddingHorizontal: 2,
    paddingVertical: 2,
    shadowColor: colors.foreground,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 10,
  },
  bottomNavCompact: { height: 61 },
  // Kept as the bar's own wrapper. The "Play Adventure" pill briefly rendered inside it, anchored
  // to this edge; it is now AdventureChargeProvider's full-screen popup instead, because blurring
  // the page behind it is not something the bar can do to what is drawn above it.
  dock: { position: 'relative' },
  navArtwork: { borderRadius: radius.lg, height: '100%', width: '100%' },
  navItem: {
    alignItems: 'center',
    aspectRatio: 1,
    backgroundColor: colors.surface1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderWidth: 1,
    elevation: 4,
    height: '93%',
    justifyContent: 'center',
    padding: 2,
    shadowColor: colors.foreground,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.13,
    shadowRadius: 7,
  },
  navItemDisabled: { opacity: 0.48 },
  navItemPressed: {
    elevation: 1,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 2,
    transform: [{ translateY: 2 }],
  },
  navItemSelected: {
    borderColor: colors.primarySoft,
    elevation: 6,
    shadowColor: colors.primaryShadow,
    shadowOffset: { width: 0, height: 5 },
    shadowOpacity: 0.2,
    shadowRadius: 9,
  },
});
