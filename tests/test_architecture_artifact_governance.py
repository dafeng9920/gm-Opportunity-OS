import unittest
from pathlib import Path
class ArchitectureArtifactGovernanceTests(unittest.TestCase):
    def test_generated_artifacts_are_ignored_and_engine_uses_distinct_names(self):
        ignore = Path('.gitignore').read_text(encoding='utf-8-sig')
        self.assertIn('docs/generated/', ignore)
        source = Path('architecture/engine.py').read_text(encoding='utf-8-sig')
        for name in ('system-fact-architecture.mmd', 'component-lifecycle.mmd', 'runtime-topology.mmd', 'candidate-state.mmd'):
            self.assertIn(name, source)
        for old_name in ('"fact-architecture.mmd"', '"lifecycle.mmd"', '"runtime.mmd"'):
            self.assertNotIn(old_name, source)
