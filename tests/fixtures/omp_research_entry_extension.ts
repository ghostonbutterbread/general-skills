import { registerResearchTool } from '../../skills/safe-fetch/scripts/omp_research_extension';
export default function (pi: any) {
  const hooks = (globalThis as any).__researchFixture;
  if (!hooks) throw Error('offline fixture hooks missing');
  registerResearchTool(pi, hooks);
}
