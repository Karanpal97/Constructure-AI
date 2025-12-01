"""Tests for Gmail service utilities."""

import pytest
from app.services.gmail import parse_email_headers, extract_sender_info, decode_email_body


class TestParseEmailHeaders:
    """Tests for email header parsing."""
    
    def test_parse_basic_headers(self):
        """Test parsing basic email headers."""
        headers = [
            {"name": "From", "value": "John Doe <john@example.com>"},
            {"name": "Subject", "value": "Test Email"},
            {"name": "Date", "value": "Mon, 1 Dec 2025 10:00:00 +0000"},
        ]
        
        result = parse_email_headers(headers)
        
        assert result["from"] == "John Doe <john@example.com>"
        assert result["subject"] == "Test Email"
        assert result["date"] == "Mon, 1 Dec 2025 10:00:00 +0000"
    
    def test_parse_empty_headers(self):
        """Test parsing empty headers list."""
        result = parse_email_headers([])
        assert result == {}
    
    def test_parse_headers_case_insensitive(self):
        """Test that header names are lowercased."""
        headers = [
            {"name": "FROM", "value": "test@example.com"},
            {"name": "SUBJECT", "value": "Test"},
        ]
        
        result = parse_email_headers(headers)
        
        assert "from" in result
        assert "subject" in result


class TestExtractSenderInfo:
    """Tests for sender info extraction."""
    
    def test_extract_name_and_email(self):
        """Test extracting name and email from standard format."""
        name, email = extract_sender_info("John Doe <john@example.com>")
        
        assert name == "John Doe"
        assert email == "john@example.com"
    
    def test_extract_quoted_name(self):
        """Test extracting quoted name."""
        name, email = extract_sender_info('"John Doe" <john@example.com>')
        
        assert name == "John Doe"
        assert email == "john@example.com"
    
    def test_extract_email_only(self):
        """Test when only email is provided."""
        name, email = extract_sender_info("john@example.com")
        
        assert name == "john@example.com"
        assert email == "john@example.com"
    
    def test_extract_empty_name(self):
        """Test when name part is empty."""
        name, email = extract_sender_info("<john@example.com>")
        
        assert name == "john@example.com"
        assert email == "john@example.com"


class TestDecodeEmailBody:
    """Tests for email body decoding."""
    
    def test_decode_simple_body(self):
        """Test decoding simple base64 body."""
        import base64
        
        original = "Hello, World!"
        encoded = base64.urlsafe_b64encode(original.encode()).decode()
        
        payload = {
            "body": {"data": encoded}
        }
        
        result = decode_email_body(payload)
        assert result == original
    
    def test_decode_multipart_text_plain(self):
        """Test decoding multipart with text/plain."""
        import base64
        
        original = "Plain text content"
        encoded = base64.urlsafe_b64encode(original.encode()).decode()
        
        payload = {
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": encoded}
                }
            ]
        }
        
        result = decode_email_body(payload)
        assert result == original
    
    def test_decode_empty_payload(self):
        """Test decoding empty payload."""
        result = decode_email_body({})
        assert result == ""
    
    def test_decode_fallback_to_html(self):
        """Test fallback to HTML when no plain text."""
        import base64
        
        html_content = "<p>HTML content</p>"
        encoded = base64.urlsafe_b64encode(html_content.encode()).decode()
        
        payload = {
            "parts": [
                {
                    "mimeType": "text/html",
                    "body": {"data": encoded}
                }
            ]
        }
        
        result = decode_email_body(payload)
        assert result == html_content

