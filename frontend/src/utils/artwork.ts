/**
 * Every bundled image the learner UI draws, in one place.
 *
 * WHY A REGISTRY. These are preloaded during the splash screen so a screen never paints before its
 * artwork is decoded (see app/_layout.tsx). A preload list kept separately from the `require`s it
 * is meant to cover drifts the moment someone adds an image, and the symptom of that drift -- one
 * picture popping in a beat late -- is exactly the bug this is here to stop. So the screens import
 * from here and the preloader walks this same object: the list cannot fall out of step with what
 * is actually rendered.
 *
 * Only artwork drawn INSIDE the app belongs here. The launcher icon, the splash image and the web
 * favicon are named in app.json and consumed by the native launcher, never by a React tree.
 *
 * WHY THESE ARE .webp (FE-017, 2026-10-09). They were PNG, 9.0 MB of assets, five of them over
 * 1 MB each -- and those five were PNG colour type 2: RGB with no alpha channel at all. A lossless
 * format was buying transparency none of them had. Re-encoded as WebP at q92 they total 405 KB
 * instead of 6423 KB, and the six tab icons 26 KB instead of 303 KB.
 *
 * MEASURED, not assumed. Every file was compared against its original with ImageMagick's DSSIM
 * (0 = identical): 0.005-0.011 for the five large images, and 0.001-0.009 for the tab icons once
 * both sides were flattened onto the app background -- the unflattened figure is a constant 0.125
 * even for a LOSSLESS re-encode, so it measures ImageMagick's alpha handling rather than anything
 * visible. Dimensions are byte-identical to the originals, which is load-bearing: the aspect
 * ratios 1672/941, 941/1672 and 1916/821 are hardcoded in nine places across the screens, so a
 * resize would have silently broken every one of them. Format changed, geometry untouched.
 *
 * The PNG originals are in git history if a different encoding is ever wanted. Do NOT convert
 * app.json's icon/splash/adaptive-icon images: those are consumed by the native launcher and
 * prebuild, which want PNG.
 */
export const artwork = {
  /**
   * The Component C task card's background pattern. 887x1774 -- authored at exactly the card's own
   * 1:2 ratio (`TASK_PANEL_ASPECT_RATIO`), so it fills the card with no cropping at any viewport.
   *
   * Converted PNG -> WebP q92 on the same terms as the images below: 1_194_167 -> 43_394 bytes
   * (96% smaller), dimensions byte-identical at 887x1774, DSSIM 0.0057 -- inside the 0.005-0.011
   * band already measured for the five large images. Geometry is load-bearing here for the same
   * reason it is for them: the card pins this exact ratio.
   */
  cTaskBackground: require('../../assets/images/c-task-background.webp'),
  heroSection: require('../../assets/images/hero-section.webp'),
  learningPath: require('../../assets/images/learning-path.webp'),
  mathmingoHeader: require('../../assets/images/mathmingo-header.webp'),
  prepareHero: require('../../assets/images/prepare-hero.webp'),
  startGame: require('../../assets/images/StartGame.webp'),
  tabGame: require('../../assets/images/tabs/game.webp'),
  tabGameSelected: require('../../assets/images/tabs/game-selected.webp'),
  tabHome: require('../../assets/images/tabs/home.webp'),
  tabHomeSelected: require('../../assets/images/tabs/home-selected.webp'),
  tabProfile: require('../../assets/images/tabs/profile.webp'),
  tabProfileSelected: require('../../assets/images/tabs/profile-selected.webp'),
} as const;

/** Every entry above. Kept as the completeness check the two lists below are derived from. */
export const allArtwork: readonly number[] = Object.values(artwork);

/**
 * WHAT THE SPLASH ACTUALLY WAITS FOR (FE-015, 2026-10-09).
 *
 * The splash used to await `allArtwork` -- all eleven images, ~7.6 MB. Two of them, together
 * ~2.8 MB (37% of the preload), are drawn by NEITHER of the screens a cold start can land on, so
 * the child was held on the splash while a hero for a screen they had not asked for yet decoded.
 *
 * The split is by "can the first frame after the splash need this", not by size:
 *
 *   - the header bar and the tab bar are in app/(learner)/_layout.tsx, so they are on screen for
 *     every learner route;
 *   - `learningPath` is Home's path panel, which is Home's entire content;
 *   - `heroSection` IS critical despite `learner-home-screen.tsx`'s `showHero` sometimes being
 *     false. That flag is only false once `heroDismissedThisAppSession` has been set, which cannot
 *     have happened on the launch that shows a splash. A cold start always draws the hero.
 *
 * Everything else is warmed AFTER the splash is down (see app/_layout.tsx), and is additionally
 * nudged at the moment the child commits to the screen that needs it -- `prepareHero` when
 * Component B is chosen, `startGame` when Play is pressed -- so the deferral is not a gamble on
 * the warm-up having finished.
 */
export const criticalArtwork: readonly number[] = [
  artwork.mathmingoHeader,
  artwork.learningPath,
  artwork.heroSection,
  artwork.tabGame,
  artwork.tabGameSelected,
  artwork.tabHome,
  artwork.tabHomeSelected,
  artwork.tabProfile,
  artwork.tabProfileSelected,
];

/**
 * Warmed after the splash is down; never blocks first paint.
 *
 * `cTaskBackground` belongs here on the same test the others are judged by -- "can the first frame
 * after the splash need this". A cold start lands on Home, never inside a Component C task, which
 * is reached through Play. It is warmed alongside `startGame` at the moment Play is pressed, so by
 * the time a task is drawn the pattern is already decoded. At 43 KB it is also the cheapest entry
 * in the registry, so deferring it costs nothing even if that nudge is ever missed.
 */
export const deferredArtwork: readonly number[] = [
  artwork.prepareHero,
  artwork.startGame,
  artwork.cTaskBackground,
];
