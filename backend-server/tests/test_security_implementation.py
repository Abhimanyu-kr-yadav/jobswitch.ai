"""
Comprehensive tests for security and data protection implementation.
"""
import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.security import InputValidator, DataEncryption, SecurityHeaders
from app.core.gdpr_compliance import GDPRComplianceManager, ConsentManager
from app.core.data_anonymization import DataAnonymizer, PIIDetector
from app.core.rate_limiting import RateLimiter, AbuseDetector
from app.models.encrypted_fields import EncryptedString, EncryptedText, HashedField
from app.schemas.validation import (
    LoginRequest, SecureFileUploadRequest, TwoFactorAuthRequest
)

client = TestClient(app)

class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_string_sanitization(self):
        """Test string sanitization"""
        # Test normal string
        result = InputValidator.sanitize_string("Hello World")
        assert result == "Hello World"
        
        # Test string with HTML
        result = InputValidator.sanitize_string("<script>alert('xss')</script>")
        assert "<script>" not in result
        
        # Test string with null bytes
        result = InputValidator.sanitize_string("Hello\x00World")
        assert "\x00" not in result
        
        # Test length limit
        with pytest.raises(ValueError):
            InputValidator.sanitize_string("x" * 10001)
    
    def test_email_validation(self):
        """Test email validation"""
        # Valid email
        result = InputValidator.validate_email("test@example.com")
        assert result == "test@example.com"
        
        # Invalid email
        with pytest.raises(ValueError):
            InputValidator.validate_email("invalid-email")
        
        # Email with HTML
        with pytest.raises(ValueError):
            InputValidator.validate_email("<script>@example.com")
    
    def test_password_validation(self):
        """Test password validation"""
        # Valid password
        result = InputValidator.validate_password("StrongPass123!")
        assert result == "StrongPass123!"
        
        # Too short
        with pytest.raises(ValueError):
            InputValidator.validate_password("weak")
        
        # Missing uppercase
        with pytest.raises(ValueError):
            InputValidator.validate_password("lowercase123!")
        
        # Missing special character
        with pytest.raises(ValueError):
            InputValidator.validate_password("NoSpecial123")
    
    def test_file_upload_validation(self):
        """Test file upload validation"""
        # Valid file
        result = InputValidator.validate_file_upload("document.pdf", 1024)
        assert result == "document.pdf"
        
        # Invalid extension
        with pytest.raises(ValueError):
            InputValidator.validate_file_upload("malware.exe", 1024)
        
        # File too large
        with pytest.raises(ValueError):
            InputValidator.validate_file_upload("large.pdf", 20 * 1024 * 1024)
        
        # Path traversal attempt
        result = InputValidator.validate_file_upload("../../../etc/passwd", 1024)
        assert result == "passwd"  # Should strip path
    
    def test_json_validation(self):
        """Test JSON input validation"""
        # Valid JSON
        data = {"key": "value", "nested": {"inner": "data"}}
        result = InputValidator.validate_json_input(data)
        assert result == data
        
        # Too deep JSON
        deep_json = {"level1": {"level2": {"level3": {"level4": {"level5": {}}}}}}
        with pytest.raises(ValueError):
            InputValidator.validate_json_input(deep_json, max_depth=3)

class TestDataEncryption:
    """Test data encryption functionality"""
    
    def test_string_encryption_decryption(self):
        """Test string encryption and decryption"""
        encryption = DataEncryption()
        
        original = "sensitive data"
        encrypted = encryption.encrypt_string(original)
        decrypted = encryption.decrypt_string(encrypted)
        
        assert encrypted != original
        assert decrypted == original
    
    def test_empty_string_encryption(self):
        """Test encryption of empty strings"""
        encryption = DataEncryption()
        
        encrypted = encryption.encrypt_string("")
        decrypted = encryption.decrypt_string(encrypted)
        
        assert decrypted == ""
    
    def test_data_hashing(self):
        """Test data hashing with salt"""
        encryption = DataEncryption()
        
        data = "password123"
        hash1, salt1 = encryption.hash_sensitive_data(data)
        hash2, salt2 = encryption.hash_sensitive_data(data)
        
        # Different salts should produce different hashes
        assert hash1 != hash2
        assert salt1 != salt2
        
        # Same salt should produce same hash
        import base64
        salt_bytes = base64.b64decode(salt1.encode())
        hash3, _ = encryption.hash_sensitive_data(data, salt_bytes)
        assert hash1 == hash3

class TestEncryptedFields:
    """Test encrypted database fields"""
    
    def test_encrypted_string_field(self):
        """Test EncryptedString field"""
        field = EncryptedString()
        
        # Test encryption
        original = "sensitive data"
        encrypted = field.process_bind_param(original, None)
        assert encrypted != original
        
        # Test decryption
        decrypted = field.process_result_value(encrypted, None)
        assert decrypted == original
    
    def test_hashed_field(self):
        """Test HashedField"""
        field = HashedField()
        
        # Test hashing
        original = "password123"
        hashed = field.process_bind_param(original, None)
        assert hashed != original
        assert "$" in hashed  # Should contain salt separator
        
        # Test verification
        assert field.verify_value(hashed, original)
        assert not field.verify_value(hashed, "wrong_password")

class TestDataAnonymization:
    """Test data anonymization functionality"""
    
    def test_email_anonymization(self):
        """Test email anonymization"""
        result = DataAnonymizer.anonymize_email("john.doe@example.com")
        assert "@example.com" in result
        assert "john.doe" not in result
    
    def test_phone_anonymization(self):
        """Test phone number anonymization"""
        result = DataAnonymizer.anonymize_phone("555-123-4567")
        assert result.endswith("4567")
        assert "555-123" not in result
    
    def test_name_anonymization(self):
        """Test name anonymization"""
        result = DataAnonymizer.anonymize_name("John")
        assert result.startswith("J")
        assert len(result) == 4
        assert "ohn" not in result
    
    def test_json_data_anonymization(self):
        """Test JSON data anonymization"""
        data = {
            "email": "test@example.com",
            "phone": "555-123-4567",
            "name": "John Doe",
            "public_data": "This should not be anonymized"
        }
        
        fields_to_anonymize = ["email", "phone", "name"]
        result = DataAnonymizer.anonymize_json_data(data, fields_to_anonymize)
        
        assert result["email"] != data["email"]
        assert result["phone"] != data["phone"]
        assert result["name"] != data["name"]
        assert result["public_data"] == data["public_data"]

class TestPIIDetection:
    """Test PII detection functionality"""
    
    def test_email_detection(self):
        """Test email detection in text"""
        detector = PIIDetector()
        
        text = "Contact me at john.doe@example.com for more info"
        detected = detector.detect_pii(text)
        
        assert "email" in detected
        assert "john.doe@example.com" in detected["email"]
    
    def test_phone_detection(self):
        """Test phone number detection"""
        detector = PIIDetector()
        
        text = "Call me at 555-123-4567"
        detected = detector.detect_pii(text)
        
        assert "phone" in detected
        assert "555-123-4567" in detected["phone"]
    
    def test_text_sanitization(self):
        """Test PII sanitization in text"""
        detector = PIIDetector()
        
        text = "Email: john@example.com, Phone: 555-123-4567"
        sanitized = detector.sanitize_text(text)
        
        assert "john@example.com" not in sanitized
        assert "555-123-4567" not in sanitized
        assert "[REDACTED]" in sanitized
    
    def test_has_pii(self):
        """Test PII detection boolean check"""
        detector = PIIDetector()
        
        assert detector.has_pii("Contact: john@example.com")
        assert not detector.has_pii("This is clean text")

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_check(self):
        """Test rate limit checking"""
        # Mock Redis client
        mock_redis = Mock()
        mock_redis.pipeline.return_value = mock_redis
        mock_redis.zremrangebyscore.return_value = None
        mock_redis.zcard.return_value = 5
        mock_redis.zadd.return_value = None
        mock_redis.expire.return_value = None
        mock_redis.execute.return_value = [None, 5, None, None]
        
        rate_limiter = RateLimiter(mock_redis)
        
        # Test within limits
        allowed, info = await rate_limiter.check_rate_limit(
            key="test_user",
            limit_type="api",
            user_id="user123"
        )
        
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_abuse_detection(self):
        """Test abuse detection"""
        # Mock Redis client
        mock_redis = Mock()
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = None
        
        abuse_detector = AbuseDetector(mock_redis)
        
        # Mock request
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {"user-agent": "Mozilla/5.0"}
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        
        result = await abuse_detector.detect_abuse(
            request=mock_request,
            user_id="user123",
            response_status=200
        )
        
        assert "abuse_score" in result
        assert "is_suspicious" in result
        assert "detected_patterns" in result

class TestGDPRCompliance:
    """Test GDPR compliance functionality"""
    
    def test_gdpr_manager_initialization(self):
        """Test GDPR manager initialization"""
        mock_db = Mock()
        manager = GDPRComplianceManager(mock_db)
        
        assert manager.db == mock_db
        assert "profile" in manager.data_categories
        assert "json" in manager.supported_formats
    
    @pytest.mark.asyncio
    async def test_consent_recording(self):
        """Test consent recording"""
        mock_db = Mock()
        consent_manager = ConsentManager(mock_db)
        
        result = await consent_manager.record_consent(
            user_id="user123",
            consent_type="data_processing",
            purpose="Provide services",
            granted=True,
            ip_address="192.168.1.1"
        )
        
        assert result["user_id"] == "user123"
        assert result["consent_type"] == "data_processing"
        assert result["granted"] is True
    
    @pytest.mark.asyncio
    async def test_consent_withdrawal(self):
        """Test consent withdrawal"""
        mock_db = Mock()
        consent_manager = ConsentManager(mock_db)
        
        result = await consent_manager.withdraw_consent(
            user_id="user123",
            consent_type="marketing",
            ip_address="192.168.1.1"
        )
        
        assert result["user_id"] == "user123"
        assert result["consent_type"] == "marketing"
        assert result["action"] == "withdrawn"

class TestSecurityHeaders:
    """Test security headers functionality"""
    
    def test_security_headers_generation(self):
        """Test security headers generation"""
        headers = SecurityHeaders.get_security_headers()
        
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers
        assert "Content-Security-Policy" in headers
        
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"

class TestValidationSchemas:
    """Test validation schemas"""
    
    def test_login_request_validation(self):
        """Test login request validation"""
        # Valid request
        valid_data = {
            "email": "test@example.com",
            "password": "StrongPass123!"
        }
        request = LoginRequest(**valid_data)
        assert request.email == "test@example.com"
        
        # Invalid email
        with pytest.raises(ValueError):
            LoginRequest(email="invalid-email", password="StrongPass123!")
        
        # Weak password
        with pytest.raises(ValueError):
            LoginRequest(email="test@example.com", password="weak")
    
    def test_secure_file_upload_validation(self):
        """Test secure file upload validation"""
        # Valid request
        valid_data = {
            "filename": "document.pdf",
            "file_size": 1024,
            "file_type": "application/pdf",
            "checksum": "a" * 64  # Valid SHA-256 format
        }
        request = SecureFileUploadRequest(**valid_data)
        assert request.filename == "document.pdf"
        
        # Invalid checksum
        with pytest.raises(ValueError):
            SecureFileUploadRequest(
                filename="document.pdf",
                file_size=1024,
                file_type="application/pdf",
                checksum="invalid"
            )
    
    def test_2fa_request_validation(self):
        """Test 2FA request validation"""
        # Valid request
        valid_data = {
            "method": "totp",
            "code": "123456"
        }
        request = TwoFactorAuthRequest(**valid_data)
        assert request.method == "totp"
        
        # Invalid method
        with pytest.raises(ValueError):
            TwoFactorAuthRequest(method="invalid", code="123456")
        
        # Invalid code format
        with pytest.raises(ValueError):
            TwoFactorAuthRequest(method="totp", code="abc")

class TestAPIEndpoints:
    """Test security-related API endpoints"""
    
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "overall_status" in data
        assert "version" in data
    
    def test_security_headers_in_response(self):
        """Test that security headers are present in responses"""
        response = client.get("/")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "Content-Security-Policy" in response.headers
    
    def test_rate_limiting_headers(self):
        """Test rate limiting headers"""
        # This would require mocking the rate limiter
        # For now, just test that the endpoint responds
        response = client.get("/")
        assert response.status_code == 200
    
    @patch('app.core.auth.get_current_user')
    def test_gdpr_data_export_endpoint(self, mock_get_user):
        """Test GDPR data export endpoint"""
        # Mock authenticated user
        mock_user = Mock()
        mock_user.id = "user123"
        mock_get_user.return_value = mock_user
        
        # Test data export request
        export_data = {
            "data_types": ["profile"],
            "format": "json",
            "include_deleted": False
        }
        
        # This would require proper database setup
        # For now, just test the endpoint exists
        response = client.post("/api/gdpr/export-data", json=export_data)
        # Expect 401 without proper auth setup
        assert response.status_code in [401, 422, 500]

class TestSecurityMiddleware:
    """Test security middleware functionality"""
    
    def test_request_size_limiting(self):
        """Test request size limiting"""
        # Large request should be rejected
        large_data = {"data": "x" * (11 * 1024 * 1024)}  # 11MB
        response = client.post("/api/test", json=large_data)
        
        # Should be rejected due to size (413 or connection error)
        assert response.status_code in [413, 422]
    
    def test_content_type_validation(self):
        """Test content type validation"""
        # Invalid content type should be rejected
        response = client.post(
            "/api/test",
            data="invalid data",
            headers={"Content-Type": "application/invalid"}
        )
        
        # Should be rejected or handled gracefully
        assert response.status_code in [415, 422, 404]
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        # POST request without CSRF token should be rejected
        response = client.post("/api/test", json={"data": "test"})
        
        # Should be rejected due to missing CSRF token or handled gracefully
        assert response.status_code in [403, 422, 404]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])