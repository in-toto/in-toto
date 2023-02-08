import unittest
from in_toto.resolver._resolver import Resolver


class Test_ApplyExcludePatterns(unittest.TestCase):
  """Test _apply_exclude_patterns(names, exclude_patterns) """

  def test_resolver_apply_exclude_explict(self):
    names = ["foo", "bar", "baz"]
    patterns = ["foo", "bar"]
    expected = ["baz"]
    result = Resolver.apply_exclude_patterns(names, patterns)
    self.assertListEqual(sorted(result), sorted(expected))

  def test_apply_exclude_all(self):
    names = ["foo", "bar", "baz"]
    patterns = ["*"]
    expected = []
    result = Resolver.apply_exclude_patterns(names, patterns)
    self.assertListEqual(sorted(result), sorted(expected))

  def test_apply_exclude_multiple_star(self):
    names = ["foo", "bar", "baz"]
    patterns = ["*a*"]
    expected = ["foo"]
    result = Resolver.apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)

  def test_apply_exclude_question_mark(self):
    names = ["foo", "bazfoo", "barfoo"]
    patterns = ["ba?foo"]
    expected = ["foo"]
    result = Resolver.apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)

  def test_apply_exclude_seq(self):
    names = ["baxfoo", "bazfoo", "barfoo"]
    patterns = ["ba[xz]foo"]
    expected = ["barfoo"]
    result = Resolver.apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)

  def test_apply_exclude_neg_seq(self):
    names = ["baxfoo", "bazfoo", "barfoo"]
    patterns = ["ba[!r]foo"]
    expected = ["barfoo"]
    result = Resolver.apply_exclude_patterns(names, patterns)
    self.assertListEqual(result, expected)
