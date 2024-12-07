import pytest
from io import BufferedReader
from pydantic import BaseModel
from python_anvil.models import FileCompatibleBaseModel
from typing import Any, Optional, List

def test_file_compat_base_model_handles_regular_data():
    class TestModel(FileCompatibleBaseModel):
        name: str
        value: int

    model = TestModel(name="test", value=42)
    data = model.model_dump()
    assert data == {"name": "test", "value": 42}

def test_file_compat_base_model_preserves_file_objects():
    class FileModel(FileCompatibleBaseModel):
        file: Any = None
    
    # Create a test file object
    with open(__file__, 'rb') as test_file:
        model = FileModel(file=test_file)
        data = model.model_dump()
        
        # First verify we got a BufferedReader back, not a SerializationIterator
        assert isinstance(data['file'], BufferedReader), \
            f"Expected BufferedReader but got {type(data['file'])}"
        
        # Verify the file is still readable
        data['file'].seek(0)
        content = data['file'].read()
        assert len(content) > 0, "File should be readable"
        
        # verify the content is the same as the original file
        with open(__file__, 'rb') as original_file:
            assert content == original_file.read(), "File content should match original"

def test_file_compat_base_model_validates_types():
    class TestModel(FileCompatibleBaseModel):
        name: str
        age: int
        
    # Should work with valid types
    model = TestModel(name="Alice", age=30)
    assert model.name == "Alice"
    assert model.age == 30
    
    # Should raise validation error for wrong types
    with pytest.raises(ValueError):
        TestModel(name="Alice", age="thirty")

def test_file_compat_base_model_handles_optional_fields():
    class TestModel(FileCompatibleBaseModel):
        required: str
        optional: Optional[str] = None
    
    # Should work with just required field
    model = TestModel(required="test")
    assert model.required == "test"
    assert model.optional is None
    
    # Should work with both fields
    model = TestModel(required="test", optional="present")
    assert model.optional == "present"

def test_file_compat_base_model_handles_nested_models():
    class NestedModel(BaseModel):
        value: str
        
    class ParentModel(FileCompatibleBaseModel):
        nested: NestedModel
        
    nested = NestedModel(value="test")
    model = ParentModel(nested=nested)
    
    data = model.model_dump()
    assert data == {"nested": {"value": "test"}}
    
def test_file_compat_base_model_handles_lists():
    class TestModel(FileCompatibleBaseModel):
        items: List[str]
        
    model = TestModel(items=["a", "b", "c"])
    data = model.model_dump()
    assert data == {"items": ["a", "b", "c"]}

def test_document_upload_handles_file_objects():
    from python_anvil.api_resources.payload import DocumentUpload, SignatureField
    
    # Create a sample signature field
    field = SignatureField(
        id="sig1",
        type="signature",
        page_num=1,
        rect={"x": 100.0, "y": 100.0, "width": 100.0}
    )
    
    # Test with a file object
    with open(__file__, 'rb') as test_file:
        doc = DocumentUpload(
            id="doc1",
            title="Test Document",
            file=test_file,
            fields=[field]
        )
        
        data = doc.model_dump()
        
        # Verify file object is preserved
        assert isinstance(data['file'], BufferedReader), \
            f"Expected BufferedReader but got {type(data['file'])}"
        
        # Verify file is still readable
        data['file'].seek(0)
        content = data['file'].read()
        assert len(content) > 0, "File should be readable"
        
        # Verify other fields are correct
        assert data['id'] == "doc1"
        assert data['title'] == "Test Document"
        assert len(data['fields']) == 1
        assert data['fields'][0]['id'] == "sig1"

def test_create_etch_packet_payload_handles_nested_file_objects():
    from python_anvil.api_resources.payload import (
        CreateEtchPacketPayload,
        DocumentUpload,
        SignatureField,
        EtchSigner,
    )
    
    # Create a sample signature field
    field = SignatureField(
        id="sig1",
        type="signature",
        page_num=1,
        rect={"x": 100.0, "y": 100.0, "width": 100.0}
    )
    
    # Create a signer
    signer = EtchSigner(
        name="Test Signer",
        email="test@example.com",
        fields=[{"file_id": "doc1", "field_id": "sig1"}]
    )
    
    # Test with a file object
    with open(__file__, 'rb') as test_file:
        # Create a DocumentUpload instance
        doc = DocumentUpload(
            id="doc1",
            title="Test Document",
            file=test_file,
            fields=[field]
        )
        
        # Create the packet payload
        packet = CreateEtchPacketPayload(
            name="Test Packet",
            signers=[signer],
            files=[doc],
            is_test=True
        )
        
        # Dump the model
        data = packet.model_dump()
        
        # Verify the structure
        assert data['name'] == "Test Packet"
        assert len(data['files']) == 1
        assert len(data['signers']) == 1
        
        # Verify file handling in the nested DocumentUpload
        file_data = data['files'][0]
        assert file_data['id'] == "doc1"
        assert file_data['title'] == "Test Document"
        assert isinstance(file_data['file'], BufferedReader), \
            f"Expected BufferedReader but got {type(file_data['file'])}"
        
        # Verify file is still readable
        file_data['file'].seek(0)
        content = file_data['file'].read()
        assert len(content) > 0, "File should be readable"
        
        # Verify the content matches the original file
        with open(__file__, 'rb') as original_file:
            assert content == original_file.read(), "File content should match original"            

def test_create_etch_packet_payload_handles_multiple_files():
    from python_anvil.api_resources.payload import (
        CreateEtchPacketPayload,
        DocumentUpload,
        SignatureField,
        EtchSigner,
    )
    
    # Create signature fields
    field1 = SignatureField(
        id="sig1",
        type="signature",
        page_num=1,
        rect={"x": 100.0, "y": 100.0, "width": 100.0}
    )
    
    field2 = SignatureField(
        id="sig2",
        type="signature",
        page_num=1,
        rect={"x": 200.0, "y": 200.0, "width": 100.0}
    )
    
    signer = EtchSigner(
        name="Test Signer",
        email="test@example.com",
        fields=[
            {"file_id": "doc1", "field_id": "sig1"},
            {"file_id": "doc2", "field_id": "sig2"}
        ]
    )
    
    # Test with multiple file objects
    with open(__file__, 'rb') as test_file1, open(__file__, 'rb') as test_file2:
        doc1 = DocumentUpload(
            id="doc1",
            title="Test Document 1",
            file=test_file1,
            fields=[field1]
        )
        
        doc2 = DocumentUpload(
            id="doc2",
            title="Test Document 2",
            file=test_file2,
            fields=[field2]
        )
        
        packet = CreateEtchPacketPayload(
            name="Test Packet",
            signers=[signer],
            files=[doc1, doc2],
            is_test=True
        )
        
        data = packet.model_dump()
        
        # Verify structure
        assert len(data['files']) == 2
        
        # Verify both files are properly handled
        for i, file_data in enumerate(data['files'], 1):
            assert file_data['id'] == f"doc{i}"
            assert file_data['title'] == f"Test Document {i}"
            assert isinstance(file_data['file'], BufferedReader), \
                f"File {i}: Expected BufferedReader but got {type(file_data['file'])}"
            
            # Verify file is readable
            file_data['file'].seek(0)
            content = file_data['file'].read()
            assert len(content) > 0, f"File {i} should be readable"
