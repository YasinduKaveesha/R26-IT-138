import { Stack, usePathname } from 'expo-router';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AdventureChargeProvider } from '@/src/features/navigation/adventure-charge-context';
import { LearnerTabBar } from '@/src/features/navigation/learner-tab-bar';
import { colors } from '@/src/theme/tokens';

/**
 * Which tab the bar should show as current, or `null` on the screens that have no bar at all --
 * the two full-screen game surfaces, which deliberately give the child nothing to navigate away
 * with except their own X button.
 */
function activeTabFor(pathname: string): 'home' | 'profile' | null {
  if (pathname.startsWith('/profile')) return 'profile';
  // The preparation screen is part of the Home journey and shows Home as current, per its own
  // original `activeTab="home"`.
  if (pathname.startsWith('/home') || pathname.startsWith('/prepare')) return 'home';
  return null;
}

export default function LearnerLayout() {
  const pathname = usePathname();
  const activeTab = activeTabFor(pathname);

  /**
   * THE TAB BAR LIVES HERE, NOT IN THE SCREENS.
   *
   * Each screen used to render its own <LearnerTabBar> as its last child. Because these screens
   * are a Stack and the bar's own buttons navigate with `router.replace`, every tab press tore the
   * whole screen down -- bar included -- and built a new one, so the bar visibly vanished and came
   * back on each move, with a blank frame in between. Mounting it once out here, OUTSIDE the
   * Stack, means the child's navigation never unmounts: only the content above it swaps.
   *
   * IT ALSO OWNS BOTH SAFE-AREA EDGES. When each screen applied the top inset itself, a freshly
   * mounted screen painted one frame with no inset and then dropped into place -- the header
   * visibly popped down on every navigation. Resolving it out here, on a view that never unmounts,
   * means there is no first frame to get wrong. Web has no insets at all, which is why this only
   * ever showed on a device.
   */
  return (
    <AdventureChargeProvider>
      <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
        <View style={styles.canvas}>
          <Stack screenOptions={{ animation: 'none', headerShown: false }} />
          {activeTab ? (
            // `activeHomePressEnabled` on the preparation screen only: there, pressing an already
            // current Home must still go back to Home, which is what that screen asked for.
            <LearnerTabBar
              activeHomePressEnabled={pathname.startsWith('/prepare')}
              activeTab={activeTab}
              playEnabled
            />
          ) : null}
        </View>
      </SafeAreaView>
    </AdventureChargeProvider>
  );
}

const styles = StyleSheet.create({
  // Mirrors the `mobileCanvas` each screen already uses, so the bar keeps the same width and
  // centring it had when it was a child of one.
  canvas: { alignSelf: 'center', flex: 1, maxWidth: 500, width: '100%' },
  safeArea: { backgroundColor: colors.background, flex: 1 },
});
