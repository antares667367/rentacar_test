import unittest
from src.app import dictify

class TestDictify(unittest.TestCase):

    def test_dictify_empty_string(self):
        result = dictify("")
        self.assertEqual(result, {})
        pass

if __name__ == '__main__':
    unittest.main()
