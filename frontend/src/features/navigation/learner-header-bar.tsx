// The learner header bar: MathMingo brand on the left, "Hi, <name>!" on the right. Extracted
// verbatim from learner-home-screen.tsx, which is now one of its two callers (the game hub is the
// other) rather than the sole owner of the markup.
//
// It is deliberately a PRESENTATION component: `displayName` comes in as a prop, and this file
// resolves no name of its own. Home and the session-preparation screen already resolve theirs from
// different sources (`me.learnerProfile.name` vs `learner.displayName`), so a header that picked
// one would silently change the other screen's greeting. Whether those two should agree is a real
// question, but it is not this extraction's to answer, and it is not answered here.
//
// The two height constants below are the ones home measures its viewport against
// (`fixedHeaderHeight = compact ? 63 : 88`). They live here, next to the styles that produce them,
// so a change to the padding and a change to the number a caller subtracts cannot drift apart.
// The game hub sizes its grid against the same pair.

import { Image } from 'expo-image';
import { StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/app-text';
import { colors, spacing, typography } from '@/src/theme/tokens';

const brandArtwork = require('../../../assets/images/mathmingo-header.png');

/** Rendered height of this bar, per density. Callers that must not scroll subtract it. */
export const LEARNER_HEADER_HEIGHT = 88;
export const LEARNER_HEADER_HEIGHT_COMPACT = 63;

export function LearnerHeaderBar({
  compact = false,
  displayName,
}: {
  compact?: boolean;
  displayName: string;
}) {
  return (
    <View style={[styles.headerGreetingSection, compact && styles.sectionCompact]}>
      <View style={styles.header}>
        <View style={styles.brand}>
          <Image
            accessibilityLabel="MathMingo"
            contentFit="contain"
            source={brandArtwork}
            style={[styles.brandArtwork, compact && styles.brandArtworkCompact]}
          />
        </View>
        <View style={styles.greeting}>
          <AppText style={[styles.greetingTitle, compact && styles.greetingTitleCompact]}>
            Hi,{' '}
            <AppText style={[styles.greetingName, compact && styles.greetingNameCompact]}>
              {displayName}!
            </AppText>
          </AppText>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  brand: { alignItems: 'center', flexDirection: 'row', flexShrink: 1, gap: 3 },
  brandArtwork: { aspectRatio: 1916 / 821, height: 68 },
  brandArtworkCompact: { height: 56 },
  greeting: { alignItems: 'flex-end', flexShrink: 1, justifyContent: 'center' },
  greetingName: { color: '#26A5FD', fontFamily: typography.fonts.heavy, fontSize: 33.75, lineHeight: 40.5 },
  greetingNameCompact: { fontSize: 28.35, lineHeight: 33.75 },
  greetingTitle: { fontFamily: typography.fonts.body, fontSize: 25, lineHeight: 30 },
  greetingTitleCompact: { fontSize: 21, lineHeight: 25 },
  header: { alignItems: 'center', flexDirection: 'row', gap: 4, justifyContent: 'space-between' },
  headerGreetingSection: {
    backgroundColor: colors.background,
    flexShrink: 0,
    paddingBottom: spacing.md,
    paddingHorizontal: spacing.smPlus,
    paddingTop: 4,
    zIndex: 10,
  },
  sectionCompact: { paddingBottom: 3 },
});
