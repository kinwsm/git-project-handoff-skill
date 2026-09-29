import unittest
from text_tools import normalize_whitespace


class NormalizeWhitespaceTests(unittest.TestCase):
    def test_plain_text(self):
        self.assertEqual(normalize_whitespace('hello world'), 'hello world')

    def test_mixed_whitespace(self):
        self.assertEqual(normalize_whitespace(' \thello\n\r world  '), 'hello world')

    def test_empty(self):
        self.assertEqual(normalize_whitespace(''), '')

    def test_whitespace_only(self):
        self.assertEqual(normalize_whitespace('\t \n'), '')

    def test_unicode_space(self):
        self.assertEqual(normalize_whitespace('你好\u3000世界'), '你好 世界')

    def test_punctuation_preserved(self):
        self.assertEqual(normalize_whitespace('a,  b!'), 'a, b!')


if __name__ == '__main__':
    unittest.main()
