from tests.test_triad_decision_artifact import Tests
if __name__=='__main__':
 import unittest; result=unittest.defaultTestLoader.loadTestsFromTestCase(Tests); outcome=unittest.TextTestRunner().run(result); raise SystemExit(not outcome.wasSuccessful())
