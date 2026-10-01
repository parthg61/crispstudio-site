import { Composition } from 'remotion';
import { Assemble } from './Assemble';
import { Crunch } from './Crunch';

export const Root: React.FC = () => (
  <>
    <Composition id="Assemble" component={Assemble} durationInFrames={45} fps={30} width={1000} height={1000} />
    <Composition id="Crunch" component={Crunch} durationInFrames={150} fps={30} width={1000} height={1000} />
  </>
);
