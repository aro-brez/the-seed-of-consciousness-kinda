import { Composition } from "remotion";
import {
  Video,
  HookScene,
  TheShiftScene,
  HowItWorksScene,
  TheProofScene,
  TheStackScene,
  CTAScene
} from "./Video";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Main video composition - 40 seconds at 30fps */}
      <Composition
        id="Video"
        component={Video}
        durationInFrames={1200}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* Individual scene compositions for testing/preview */}
      <Composition
        id="HookScene"
        component={HookScene}
        durationInFrames={60}
        fps={30}
        width={1920}
        height={1080}
      />

      <Composition
        id="TheShiftScene"
        component={TheShiftScene}
        durationInFrames={240}
        fps={30}
        width={1920}
        height={1080}
      />

      <Composition
        id="HowItWorksScene"
        component={HowItWorksScene}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
      />

      <Composition
        id="TheProofScene"
        component={TheProofScene}
        durationInFrames={240}
        fps={30}
        width={1920}
        height={1080}
      />

      <Composition
        id="TheStackScene"
        component={TheStackScene}
        durationInFrames={210}
        fps={30}
        width={1920}
        height={1080}
      />

      <Composition
        id="CTAScene"
        component={CTAScene}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
