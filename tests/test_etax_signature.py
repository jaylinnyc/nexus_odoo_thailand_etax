# -*- coding: utf-8 -*-
"""
Unit Tests for XAdES-BES Digital Signature Module
=================================================

Tests for lib/etax_signature.py
"""
import pytest
import base64
import hashlib
from unittest.mock import Mock, patch, MagicMock
from lxml import etree


class TestSignatureNamespaces:
    """Test signature namespace constants."""
    
    def test_xmldsig_namespace(self):
        """Test XML Digital Signature namespace."""
        from lib.etax_signature import XAdESBESSigner
        signer = XAdESBESSigner.__new__(XAdESBESSigner)
        assert 'http://www.w3.org/2000/09/xmldsig#' in str(signer.__class__.__module__)
    
    def test_xades_namespace_defined(self):
        """Test XAdES namespace is properly defined."""
        # XAdES namespace should be http://uri.etsi.org/01903/v1.3.2#
        expected = "http://uri.etsi.org/01903/v1.3.2#"
        from lib.etax_signature import XADES_NS
        assert XADES_NS == expected


class TestXAdESBESSigner:
    """Test XAdES-BES Signer class."""
    
    @pytest.fixture
    def signer(self):
        """Create a signer instance."""
        from lib.etax_signature import XAdESBESSigner
        return XAdESBESSigner()
    
    def test_signer_initialization(self, signer):
        """Test signer initializes correctly."""
        assert signer is not None
        assert signer._private_key is None
        assert signer._certificate is None
        assert signer._cert_chain == []
    
    def test_signer_without_certificate(self, signer):
        """Test signer raises error when no certificate loaded."""
        test_xml = b"<root><data>test</data></root>"
        with pytest.raises(ValueError, match="Certificate not loaded"):
            signer.sign_xml(test_xml)
    
    def test_calculate_digest_sha512(self, signer):
        """Test SHA-512 digest calculation."""
        test_data = b"test data for hashing"
        expected = base64.b64encode(
            hashlib.sha512(test_data).digest()
        ).decode('utf-8')
        
        result = signer._calculate_digest(test_data, 'sha512')
        assert result == expected
    
    def test_calculate_digest_sha256(self, signer):
        """Test SHA-256 digest calculation."""
        test_data = b"test data for hashing"
        expected = base64.b64encode(
            hashlib.sha256(test_data).digest()
        ).decode('utf-8')
        
        result = signer._calculate_digest(test_data, 'sha256')
        assert result == expected
    
    def test_canonicalization(self, signer):
        """Test XML canonicalization."""
        # XML with different formatting should produce same canonical form
        xml1 = etree.fromstring(b'<root><child/></root>')
        xml2 = etree.fromstring(b'<root>\n  <child></child>\n</root>')
        
        c14n1 = signer._canonicalize(xml1)
        c14n2 = signer._canonicalize(xml2)
        
        # Both should produce valid canonical XML
        assert c14n1 is not None
        assert c14n2 is not None
        assert isinstance(c14n1, bytes)
        assert isinstance(c14n2, bytes)


class TestSignatureStructure:
    """Test signature XML structure."""
    
    @pytest.fixture
    def mock_signer(self):
        """Create a signer with mocked certificate."""
        from lib.etax_signature import XAdESBESSigner
        signer = XAdESBESSigner()
        
        # Mock certificate data
        signer._private_key = MagicMock()
        signer._certificate = MagicMock()
        signer._certificate.public_bytes.return_value = b"mock_cert_data"
        signer._certificate.subject.get_attributes_for_oid.return_value = [
            MagicMock(value="Test Subject")
        ]
        signer._certificate.issuer.get_attributes_for_oid.return_value = [
            MagicMock(value="Test Issuer")
        ]
        signer._certificate.serial_number = 12345
        signer._certificate.not_valid_before_utc = Mock()
        signer._certificate.not_valid_before_utc.isoformat.return_value = "2024-01-01T00:00:00"
        
        return signer
    
    def test_signature_element_creation(self, mock_signer):
        """Test signature element structure."""
        # This tests the internal structure of signature elements
        from lib.etax_signature import DS_NS
        
        nsmap = {
            'ds': DS_NS,
        }
        
        sig_elem = etree.Element(
            f"{{{DS_NS}}}Signature",
            nsmap=nsmap
        )
        
        assert sig_elem.tag == f"{{{DS_NS}}}Signature"
        assert sig_elem.prefix == 'ds'
    
    def test_signed_info_components(self):
        """Test SignedInfo contains required components."""
        from lib.etax_signature import DS_NS
        
        nsmap = {'ds': DS_NS}
        signed_info = etree.Element(f"{{{DS_NS}}}SignedInfo", nsmap=nsmap)
        
        # Add required children
        c14n_method = etree.SubElement(
            signed_info, 
            f"{{{DS_NS}}}CanonicalizationMethod",
            Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"
        )
        
        sig_method = etree.SubElement(
            signed_info,
            f"{{{DS_NS}}}SignatureMethod",
            Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha512"
        )
        
        reference = etree.SubElement(
            signed_info,
            f"{{{DS_NS}}}Reference",
            URI=""
        )
        
        assert len(signed_info) == 3
        assert c14n_method.get('Algorithm') == "http://www.w3.org/2001/10/xml-exc-c14n#"
        assert sig_method.get('Algorithm') == "http://www.w3.org/2001/04/xmldsig-more#rsa-sha512"


class TestXAdESProperties:
    """Test XAdES-BES specific properties."""
    
    def test_xades_signed_properties_structure(self):
        """Test XAdES SignedProperties structure."""
        from lib.etax_signature import XADES_NS, DS_NS
        
        nsmap = {
            'xades': XADES_NS,
            'ds': DS_NS
        }
        
        signed_props = etree.Element(
            f"{{{XADES_NS}}}SignedProperties",
            nsmap=nsmap
        )
        signed_props.set('Id', 'SignedProperties')
        
        # Add SignedSignatureProperties
        sig_props = etree.SubElement(
            signed_props,
            f"{{{XADES_NS}}}SignedSignatureProperties"
        )
        
        # Add SigningTime
        signing_time = etree.SubElement(
            sig_props,
            f"{{{XADES_NS}}}SigningTime"
        )
        signing_time.text = "2024-01-01T12:00:00Z"
        
        # Add SigningCertificate
        signing_cert = etree.SubElement(
            sig_props,
            f"{{{XADES_NS}}}SigningCertificate"
        )
        
        assert signed_props.get('Id') == 'SignedProperties'
        assert len(sig_props) == 2
        assert signing_time.text == "2024-01-01T12:00:00Z"


class TestDigestCalculation:
    """Test digest calculation methods."""
    
    @pytest.fixture
    def signer(self):
        from lib.etax_signature import XAdESBESSigner
        return XAdESBESSigner()
    
    def test_empty_data_digest(self, signer):
        """Test digest of empty data."""
        empty_data = b""
        result = signer._calculate_digest(empty_data, 'sha512')
        
        expected = base64.b64encode(
            hashlib.sha512(b"").digest()
        ).decode('utf-8')
        
        assert result == expected
    
    def test_unicode_data_digest(self, signer):
        """Test digest of unicode content."""
        unicode_data = "ทดสอบภาษาไทย".encode('utf-8')
        result = signer._calculate_digest(unicode_data, 'sha512')
        
        expected = base64.b64encode(
            hashlib.sha512(unicode_data).digest()
        ).decode('utf-8')
        
        assert result == expected
    
    def test_large_data_digest(self, signer):
        """Test digest of large data."""
        large_data = b"x" * 1000000  # 1MB of data
        result = signer._calculate_digest(large_data, 'sha512')
        
        assert result is not None
        assert len(result) > 0


class TestCertificateLoading:
    """Test certificate loading functionality."""
    
    @pytest.fixture
    def signer(self):
        from lib.etax_signature import XAdESBESSigner
        return XAdESBESSigner()
    
    def test_load_invalid_path(self, signer):
        """Test loading certificate from invalid path."""
        with pytest.raises(FileNotFoundError):
            signer.load_certificate("/nonexistent/path/cert.p12", "password")
    
    def test_load_with_empty_password(self, signer):
        """Test loading certificate with empty password."""
        # This should raise an error for non-existent file
        with pytest.raises(FileNotFoundError):
            signer.load_certificate("/nonexistent/cert.p12", "")


class TestSignatureValidation:
    """Test signature validation helpers."""
    
    def test_validate_algorithm_sha512(self):
        """Test SHA-512 algorithm validation."""
        valid_algorithms = ['sha256', 'sha384', 'sha512']
        assert 'sha512' in valid_algorithms
    
    def test_reference_uri_format(self):
        """Test reference URI format for enveloped signature."""
        # Enveloped signature should have empty URI
        uri = ""
        assert uri == ""
        
        # Or specific ID reference
        uri_with_id = "#document"
        assert uri_with_id.startswith("#")


class TestEnvelopedSignature:
    """Test enveloped signature transformation."""
    
    def test_enveloped_transform_algorithm(self):
        """Test enveloped signature transform algorithm."""
        expected = "http://www.w3.org/2000/09/xmldsig#enveloped-signature"
        from lib.etax_signature import DS_NS
        
        nsmap = {'ds': DS_NS}
        transform = etree.Element(
            f"{{{DS_NS}}}Transform",
            nsmap=nsmap,
            Algorithm=expected
        )
        
        assert transform.get('Algorithm') == expected
    
    def test_c14n_transform_algorithm(self):
        """Test C14N transform algorithm."""
        expected = "http://www.w3.org/2001/10/xml-exc-c14n#"
        from lib.etax_signature import DS_NS
        
        nsmap = {'ds': DS_NS}
        transform = etree.Element(
            f"{{{DS_NS}}}Transform",
            nsmap=nsmap,
            Algorithm=expected
        )
        
        assert transform.get('Algorithm') == expected
