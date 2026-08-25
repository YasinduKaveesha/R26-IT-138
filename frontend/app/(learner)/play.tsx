// TEMPORARY DEV-PREVIEW WIRING. Real grade/session-mode selection for the Play tab belongs to a
// future Component C batch (it would come from the learner's actual classroom membership, not a
// literal here) -- c-session-logic.ts's decideSessionBootstrap deliberately never invents either
// value itself, and this route is exactly the kind of caller its own comment anticipates supplying
// them "most likely via route params". `grade={2}` / `sessionMode="c_only"` are named, visible
// constants for exercising the archetype surfaces under development against the dev fixture, not a
// claim about where a real learner's grade comes from.
import { CSessionScreen } from '@/src/features/c-session/c-session-screen';

export default function LearnerPlayRoute() {
  return <CSessionScreen grade={2} sessionMode="c_only" />;
}
