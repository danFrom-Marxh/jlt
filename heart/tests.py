from django.test import SimpleTestCase

from .templatetags.rating_tags import rating_stars


class RatingStarsTests(SimpleTestCase):
    def test_fractional_star_fill_is_exact(self):
        self.assertEqual(rating_stars(3.5), ["100", "100", "100", "50", "0"])
        self.assertEqual(rating_stars(3.6), ["100", "100", "100", "60", "0"])
        self.assertEqual(rating_stars(3.7), ["100", "100", "100", "70", "0"])

    def test_multiple_decimals_are_preserved(self):
        self.assertEqual(rating_stars("3.57"), ["100", "100", "100", "57", "0"])
        self.assertEqual(rating_stars("4.255"), ["100", "100", "100", "100", "25.5"])

    def test_localized_decimal_input_is_tolerated(self):
        self.assertEqual(rating_stars("3,6"), ["100", "100", "100", "60", "0"])
