// The Play tab's route boundary. It mounts the game hub -- the menu of the eight Component C game
// families -- and nothing else.
//
// This replaces the TEMPORARY DEV-PREVIEW WIRING that mounted `<CSessionScreen grade={2}
// sessionMode="c_only" />` directly here. That wiring existed because there was no menu to put in
// front of a session; there is one now. The grade/session-mode pair it hardcoded has not been
// deleted so much as moved to where it can be seen and chosen: each hub button carries its own
// family's grade and navigates to `/(learner)/c-session`, which already reads and validates both
// as query params. Session bootstrap still invents neither value itself.
import { GameHubScreen } from '@/src/features/game-hub/game-hub-screen';

export default function LearnerPlayRoute() {
  return <GameHubScreen />;
}
