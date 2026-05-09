import unittest

from validators import validate


class ValidateEmailTests(unittest.TestCase):
    def test_valid_email(self):
        result = validate({"email": "user@example.com"}, {"email": "email"})
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], {})

    def test_invalid_email_no_at(self):
        result = validate({"email": "userexample.com"}, {"email": "email"})
        self.assertFalse(result["valid"])
        self.assertIn("invalid email address", result["errors"]["email"])

    def test_invalid_email_no_tld(self):
        result = validate({"email": "user@example"}, {"email": "email"})
        self.assertFalse(result["valid"])


class ValidatePhoneTests(unittest.TestCase):
    def test_valid_phone_international(self):
        result = validate({"phone": "+1 (555) 123-4567"}, {"phone": "phone"})
        self.assertTrue(result["valid"])

    def test_valid_phone_digits_only(self):
        result = validate({"phone": "5551234567"}, {"phone": "phone"})
        self.assertTrue(result["valid"])

    def test_invalid_phone_too_short(self):
        result = validate({"phone": "12345"}, {"phone": "phone"})
        self.assertFalse(result["valid"])

    def test_invalid_phone_letters(self):
        result = validate({"phone": "555-CALL-NOW"}, {"phone": "phone"})
        self.assertFalse(result["valid"])


class ValidateUrlTests(unittest.TestCase):
    def test_valid_https_url(self):
        result = validate({"site": "https://example.com"}, {"site": "url"})
        self.assertTrue(result["valid"])

    def test_valid_http_url_with_path(self):
        result = validate({"site": "http://example.com/path?q=1"}, {"site": "url"})
        self.assertTrue(result["valid"])

    def test_invalid_url_no_scheme(self):
        result = validate({"site": "example.com"}, {"site": "url"})
        self.assertFalse(result["valid"])

    def test_invalid_url_ftp(self):
        result = validate({"site": "ftp://example.com"}, {"site": "url"})
        self.assertFalse(result["valid"])


class ValidateMultipleFieldsTests(unittest.TestCase):
    def test_collects_all_errors(self):
        payload = {"email": "bad", "phone": "x", "site": "nope"}
        schema = {"email": "email", "phone": "phone", "site": "url"}
        result = validate(payload, schema)
        self.assertFalse(result["valid"])
        self.assertEqual(set(result["errors"].keys()), {"email", "phone", "site"})

    def test_missing_field_reports_required(self):
        result = validate({}, {"email": "email"})
        self.assertFalse(result["valid"])
        self.assertIn("field is required", result["errors"]["email"])

    def test_unknown_validator_type_raises(self):
        with self.assertRaises(ValueError):
            validate({"x": "y"}, {"x": "ssn"})

    def test_all_valid(self):
        payload = {
            "email": "a@b.co",
            "phone": "+44 20 7946 0958",
            "site": "https://example.org",
        }
        schema = {"email": "email", "phone": "phone", "site": "url"}
        result = validate(payload, schema)
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], {})


if __name__ == "__main__":
    unittest.main()
