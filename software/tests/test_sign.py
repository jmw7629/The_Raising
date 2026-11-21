"""III.26: Lamport, one-time."""
import unittest

import helper
from raising import sign


class Lamport(helper.Case):
    seed = sign.H("fixture key|test")

    def test_sign_and_rebuild(self):
        h = sign.H("a line")
        sig = sign.sign(self.seed, 3, h)
        self.assertEqual(len(sig), 256)
        self.assertTrue(sign.wellformed(sig))
        self.assertEqual(sign.recover(sig, h), sign.public(self.seed, 3))

    def test_another_line_or_index_does_not_rebuild(self):
        h = sign.H("a line")
        sig = sign.sign(self.seed, 3, h)
        self.assertNotEqual(sign.recover(sig, sign.H("another line")), sign.public(self.seed, 3))
        self.assertNotEqual(sign.public(self.seed, 3), sign.public(self.seed, 4))
        self.assertNotEqual(sign.recover(sign.sign(self.seed, 4, h), h), sign.public(self.seed, 3))

    def test_secrets_follow_the_design_string(self):
        self.assertEqual(sign.secret("s", 2, 5, 1), sign.H("s|2|5|1"))
        bits = sign.bits("8" + "0" * 63)
        self.assertEqual((bits[0], sum(bits)), (1, 1))
        h = "8" + "0" * 63
        self.assertEqual(sign.sign("s", 0, h)[0], [sign.secret("s", 0, 0, 1), sign.H(sign.secret("s", 0, 0, 0))])

    def test_malformed(self):
        self.assertIsNone(sign.recover([["x", "y"]], sign.H("a")))
        self.assertFalse(sign.wellformed("sig"))

    def test_new_keys_differ(self):
        a, b = sign.new_key("n"), sign.new_key("n")
        self.assertEqual(len(a["seed"]), 64)
        self.assertNotEqual(a["seed"], b["seed"])


if __name__ == "__main__":
    unittest.main()
