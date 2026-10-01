import { Composition } from 'remotion';
import { Crunch } from './Crunch';

export const Root: React.FC = () => (
  <Composition id="Crunch" component={Crunch} durationInFrames={150} fps={30} width={1000} height={1000} />
);
