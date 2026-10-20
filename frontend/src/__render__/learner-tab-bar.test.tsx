/* eslint-disable import/first --
   The imports below sit AFTER the jest.mock blocks on purpose. ES imports are hoisted above const
   declarations, so moving them to the top would make the module under test load -- and its mock
   factory run -- before the `mock*` consts those factories close over are initialised, which is a
   temporal-dead-zone crash rather than a style question. */
import { fireEvent, render } from '@testing-library/react-native';

const mockRequestPlay = jest.fn();
const mockCharge = {
  awardForSession: jest.fn(),
  dismissPill: jest.fn(),
  dismissPlayPrep: jest.fn(),
  level: 0,
  maxLevel: 4,
  pillVisible: false,
  playPrepReady: false,
  preparingPlay: false,
  requestPlay: mockRequestPlay,
  startPreparedGame: jest.fn(),
};
jest.mock('@/src/features/navigation/adventure-charge-context', () => ({
  useAdventureCharge: () => mockCharge,
}));

import { router } from 'expo-router';

import { LearnerTabBar } from '@/src/features/navigation/learner-tab-bar';

describe('LearnerTabBar', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders all three tabs', async () => {
    const { getByLabelText } = await render(<LearnerTabBar activeTab="home" playEnabled />);
    expect(getByLabelText(/^Play tab/)).toBeTruthy();
    expect(getByLabelText(/^Home tab/)).toBeTruthy();
    // Labelled "compD", not "Profile" (owner request, 2026-10-20). The route and `activeTab` key
    // are both unchanged -- only the word under the icon.
    expect(getByLabelText(/^compD tab/)).toBeTruthy();
  });

  it('marks the active tab as selected and does not navigate away from it', async () => {
    const { getByLabelText } = await render(<LearnerTabBar activeTab="home" playEnabled />);
    const home = getByLabelText(/^Home tab, selected/);
    fireEvent.press(home);
    expect(router.replace).not.toHaveBeenCalled();
  });

  it('routes Play through the charge context rather than navigating itself', async () => {
    // Play is gated on the adventure battery, so the bar must not know the destination -- that
    // decision belongs to requestPlay.
    const { getByLabelText } = await render(<LearnerTabBar activeTab="home" playEnabled />);
    fireEvent.press(getByLabelText(/^Play tab/));
    expect(mockRequestPlay).toHaveBeenCalledTimes(1);
    expect(router.replace).not.toHaveBeenCalled();
  });

  it('reports Play as unavailable when it is disabled', async () => {
    const { getByLabelText } = await render(<LearnerTabBar activeTab="home" playEnabled={false} />);
    const play = getByLabelText(/^Play tab, unavailable/);
    fireEvent.press(play);
    expect(mockRequestPlay).not.toHaveBeenCalled();
  });

  it('no longer renders the Play Adventure pill, which is now the global popup', async () => {
    // It briefly lived here; blurring the page is not something the bar can do to what is drawn
    // above it, so it moved to AdventureChargeProvider. This guards against it coming back twice.
    const { queryByText } = await render(<LearnerTabBar activeTab="home" playEnabled />);
    expect(queryByText('Play Adventure')).toBeNull();
  });
});
