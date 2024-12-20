import base64
import pytest
from pydantic import BaseModel
from typing import Any, List, Optional

from python_anvil.models import FileCompatibleBaseModel


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

        # Verify we got a dictionary with the expected structure
        assert isinstance(data['file'], dict)
        assert 'data' in data['file']
        assert 'mimetype' in data['file']
        assert 'filename' in data['file']

        # Verify the content matches
        with open(__file__, 'rb') as original_file:
            original_content = original_file.read()
            decoded_content = base64.b64decode(data['file']['data'].encode('utf-8'))
            assert (
                decoded_content == original_content
            ), "File content should match original"


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
    # pylint: disable-next=import-outside-toplevel
    from python_anvil.api_resources.payload import DocumentUpload, SignatureField

    # Create a sample signature field
    field = SignatureField(
        id="sig1",
        type="signature",
        page_num=1,
        rect={"x": 100.0, "y": 100.0, "width": 100.0},
    )

    # Test with a file object
    with open(__file__, 'rb') as test_file:
        doc = DocumentUpload(
            id="doc1", title="Test Document", file=test_file, fields=[field]
        )

        data = doc.model_dump()

        # Verify file is converted to expected dictionary format
        assert isinstance(data['file'], dict)
        assert 'data' in data['file']
        assert 'mimetype' in data['file']
        assert 'filename' in data['file']

        # Verify content matches
        with open(__file__, 'rb') as original_file:
            original_content = original_file.read()
            decoded_content = base64.b64decode(data['file']['data'].encode('utf-8'))
            assert decoded_content == original_content

        # Verify other fields are correct
        assert data['id'] == "doc1"
        assert data['title'] == "Test Document"
        assert len(data['fields']) == 1
        assert data['fields'][0]['id'] == "sig1"


def test_create_etch_packet_payload_handles_nested_file_objects():
    # pylint: disable-next=import-outside-toplevel
    from python_anvil.api_resources.payload import (
        CreateEtchPacketPayload,
        DocumentUpload,
        EtchSigner,
        SignatureField,
    )

    # Create a sample signature field
    field = SignatureField(
        id="sig1",
        type="signature",
        page_num=1,
        rect={"x": 100.0, "y": 100.0, "width": 100.0},
    )

    # Create a signer
    signer = EtchSigner(
        name="Test Signer",
        email="test@example.com",
        fields=[{"file_id": "doc1", "field_id": "sig1"}],
    )

    # Test with a file object
    with open(__file__, 'rb') as test_file:
        # Create a DocumentUpload instance
        doc = DocumentUpload(
            id="doc1", title="Test Document", file=test_file, fields=[field]
        )

        # Create the packet payload
        packet = CreateEtchPacketPayload(
            name="Test Packet", signers=[signer], files=[doc], is_test=True
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
        assert isinstance(file_data['file'], dict)
        assert 'data' in file_data['file']
        assert 'mimetype' in file_data['file']
        assert 'filename' in file_data['file']

        # Verify content matches
        with open(__file__, 'rb') as original_file:
            original_content = original_file.read()
            decoded_content = base64.b64decode(
                file_data['file']['data'].encode('utf-8')
            )
            assert decoded_content == original_content


def test_create_etch_packet_payload_handles_multiple_files():
    # pylint: disable-next=import-outside-toplevel
    from python_anvil.api_resources.payload import (
        CreateEtchPacketPayload,
        DocumentUpload,
        EtchSigner,
        SignatureField,
    )

    # Create signature fields
    field1 = SignatureField(
        id="sig1",
        type="signature",
        page_num=1,
        rect={"x": 100.0, "y": 100.0, "width": 100.0},
    )

    field2 = SignatureField(
        id="sig2",
        type="signature",
        page_num=1,
        rect={"x": 200.0, "y": 200.0, "width": 100.0},
    )

    signer = EtchSigner(
        name="Test Signer",
        email="test@example.com",
        fields=[
            {"file_id": "doc1", "field_id": "sig1"},
            {"file_id": "doc2", "field_id": "sig2"},
        ],
    )

    # Test with multiple file objects
    with open(__file__, 'rb') as test_file1, open(__file__, 'rb') as test_file2:
        doc1 = DocumentUpload(
            id="doc1", title="Test Document 1", file=test_file1, fields=[field1]
        )

        doc2 = DocumentUpload(
            id="doc2", title="Test Document 2", file=test_file2, fields=[field2]
        )

        packet = CreateEtchPacketPayload(
            name="Test Packet", signers=[signer], files=[doc1, doc2], is_test=True
        )

        data = packet.model_dump()

        # Verify structure
        assert len(data['files']) == 2

        # Verify both files are properly handled
        for i, file_data in enumerate(data['files'], 1):
            assert file_data['id'] == f"doc{i}"
            assert file_data['title'] == f"Test Document {i}"
            assert isinstance(file_data['file'], dict)
            assert 'data' in file_data['file']
            assert 'mimetype' in file_data['file']
            assert 'filename' in file_data['file']

            # Verify content matches
            with open(__file__, 'rb') as original_file:
                original_content = original_file.read()
                decoded_content = base64.b64decode(
                    file_data['file']['data'].encode('utf-8')
                )
                assert decoded_content == original_content
