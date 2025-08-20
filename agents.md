# AI Agents Guide for Python-Anvil

This guide explains how AI agents can effectively use the `python-anvil` library to interact with Anvil's APIs for PDF processing, e-signatures, and workflow automation.

## Overview

The `python-anvil` library provides a Python interface to Anvil's comprehensive paperwork automation platform. AI agents can use this library to:

- **Fill PDF templates** with structured data
- **Generate PDFs** from markdown/HTML content
- **Create e-signature packets** via Etch
- **Submit workflow data** to Anvil Workflows
- **Execute GraphQL queries** for data retrieval
- **Manage file uploads** and downloads

## Installation

```bash
pip install python-anvil
```

## Authentication

AI agents need an Anvil API key to authenticate:

```python
import os
from python_anvil import Anvil

# Set API key in environment
os.environ["ANVIL_API_KEY"] = "your_api_key_here"

# Initialize client
anvil = Anvil(api_key="your_api_key_here")
```

## Core Capabilities for AI Agents

### 1. PDF Template Filling

AI agents can populate PDF templates with structured data:

```python
from python_anvil.api_resources.payload import FillPDFPayload

# Create payload with form data
payload = FillPDFPayload(
    data={
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com",
        "company": "Acme Corp"
    }
)

# Fill PDF template
result = anvil.fill_pdf(
    cast_eid="template_id_here",
    payload=payload
)

# Save filled PDF
with open("filled_document.pdf", "wb") as f:
    f.write(result)
```

### 2. PDF Generation

Generate PDFs from markdown or HTML content:

```python
from python_anvil.api_resources.payload import GeneratePDFPayload

# Create markdown content
markdown_content = """
# Contract Agreement

## Parties
- **Company**: Acme Corporation
- **Client**: John Doe

## Terms
1. Service delivery within 30 days
2. Payment due upon completion
3. 90-day warranty period
"""

# Generate PDF
result = anvil.generate_pdf(
    payload=GeneratePDFPayload(
        type="markdown",
        title="Contract Agreement",
        content=markdown_content
    )
)

# Save generated PDF
with open("contract.pdf", "wb") as f:
    f.write(result)
```

### 3. E-Signature Packet Creation

Create and manage e-signature packets via Etch:

```python
from python_anvil.api_resources.payload import CreateEtchPacketPayload

# Create signature packet
payload = CreateEtchPacketPayload(
    name="Employment Agreement",
    signers=[
        {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "routingOrder": 1
        },
        {
            "name": "Jane Smith",
            "email": "jane.smith@company.com",
            "routingOrder": 2
        }
    ],
    files=[
        {
            "id": "employment_agreement",
            "title": "Employment Agreement",
            "filename": "agreement.pdf"
        }
    ]
)

# Create the packet
result = anvil.create_etch_packet(payload=payload)
packet_id = result["data"]["createEtchPacket"]["eid"]

# Generate signing URL for first signer
sign_url = anvil.generate_etch_signing_url(
    packet_eid=packet_id,
    signer_eid=result["data"]["createEtchPacket"]["signers"][0]["eid"]
)
```

### 4. Workflow Submissions

Submit data to Anvil Workflows:

```python
from python_anvil.api_resources.payload import ForgeSubmitPayload

# Submit form data to workflow
payload = ForgeSubmitPayload(
    forge_eid="workflow_form_id",
    payload={
        "applicant_name": "John Doe",
        "position": "Software Engineer",
        "start_date": "2024-02-01",
        "salary": 85000
    }
)

# Submit to workflow
result = anvil.forge_submit(payload=payload)
submission_id = result["data"]["forgeSubmit"]["eid"]
```

### 5. GraphQL Queries

Execute custom GraphQL queries for data retrieval:

```python
# Query for workflow information
query = """
query GetWorkflow($slug: String!, $organizationSlug: String!) {
  weld(organizationSlug: $organizationSlug, slug: $slug) {
    id
    eid
    name
    title
    status
    submissions {
      id
      eid
      status
      createdAt
    }
  }
}
"""

variables = {
    "slug": "employment-onboarding",
    "organizationSlug": "acme-corp"
}

result = anvil.query(query, variables)
workflow_data = result["data"]["weld"]
```

### 6. File Management

Handle file uploads and downloads:

```python
# Upload file for e-signature packet
with open("document.pdf", "rb") as f:
    file_data = f.read()

result = anvil.upload_file(
    filename="document.pdf",
    file_data=file_data
)

file_id = result["data"]["uploadFile"]["eid"]

# Download completed document
result = anvil.download_etch_packet(packet_eid="packet_id_here")
with open("completed_document.pdf", "wb") as f:
    f.write(result)
```

## Best Practices for AI Agents

### 1. Error Handling

Implement robust error handling for API calls:

```python
try:
    result = anvil.fill_pdf(cast_eid="template_id", payload=payload)
except Exception as e:
    print(f"Error filling PDF: {e}")
    # Handle error appropriately
```

### 2. Rate Limiting

Respect API rate limits and implement backoff strategies:

```python
import time
from python_anvil.exceptions import RateLimitError

def make_api_call_with_retry(api_call, max_retries=3):
    for attempt in range(max_retries):
        try:
            return api_call()
        except RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
```

### 3. Data Validation

Validate data before sending to APIs:

```python
from python_anvil.api_resources.payload import FillPDFPayload

def validate_pdf_data(data):
    required_fields = ["firstName", "lastName", "email"]
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")
    
    return FillPDFPayload(data=data)

# Use validated payload
payload = validate_pdf_data(user_data)
result = anvil.fill_pdf(cast_eid="template_id", payload=payload)
```

### 4. Batch Processing

Handle multiple operations efficiently:

```python
def process_multiple_documents(template_id, data_list):
    results = []
    
    for data in data_list:
        try:
            payload = FillPDFPayload(data=data)
            result = anvil.fill_pdf(cast_eid=template_id, payload=payload)
            results.append({"success": True, "data": result})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    
    return results
```

## Common Use Cases for AI Agents

### 1. Document Automation

```python
def automate_contract_generation(client_data):
    # Generate contract from template
    contract_pdf = anvil.fill_pdf(
        cast_eid="contract_template_id",
        payload=FillPDFPayload(data=client_data)
    )
    
    # Create e-signature packet
    packet = anvil.create_etch_packet(
        payload=CreateEtchPacketPayload(
            name=f"Contract for {client_data['company']}",
            signers=[
                {"name": client_data["contact_name"], "email": client_data["contact_email"]}
            ],
            files=[{"id": "contract", "title": "Contract", "filename": "contract.pdf"}]
        )
    )
    
    return packet
```

### 2. Form Processing

```python
def process_application_forms(applications):
    results = []
    
    for app in applications:
        # Submit to workflow
        submission = anvil.forge_submit(
            payload=ForgeSubmitPayload(
                forge_eid="application_form_id",
                payload=app
            )
        )
        
        # Generate confirmation PDF
        confirmation = anvil.generate_pdf(
            payload=GeneratePDFPayload(
                type="markdown",
                title="Application Confirmation",
                content=f"# Application Received\n\nThank you for your application, {app['name']}!"
            )
        )
        
        results.append({
            "submission_id": submission["data"]["forgeSubmit"]["eid"],
            "confirmation_pdf": confirmation
        })
    
    return results
```

### 3. Compliance Monitoring

```python
def monitor_workflow_compliance(organization_slug):
    # Query for all workflows
    query = """
    query GetWorkflows($orgSlug: String!) {
      organization(organizationSlug: $orgSlug) {
        welds {
          id
          name
          status
          submissions {
            id
            status
            completedAt
          }
        }
      }
    }
    """
    
    result = anvil.query(query, {"orgSlug": organization_slug})
    workflows = result["data"]["organization"]["welds"]
    
    compliance_report = []
    for workflow in workflows:
        completed_submissions = [s for s in workflow["submissions"] if s["status"] == "completed"]
        compliance_report.append({
            "workflow": workflow["name"],
            "total_submissions": len(workflow["submissions"]),
            "completed_submissions": len(completed_submissions),
            "completion_rate": len(completed_submissions) / len(workflow["submissions"]) if workflow["submissions"] else 0
        })
    
    return compliance_report
```

## Environment Configuration

AI agents should configure their environment appropriately:

```python
import os
from python_anvil import Anvil

# Environment configuration
ENVIRONMENT = os.getenv("ANVIL_ENVIRONMENT", "dev")
API_KEY = os.getenv("ANVIL_API_KEY")
ENDPOINT_URL = os.getenv("ANVIL_ENDPOINT_URL")  # Optional custom endpoint

# Initialize client
anvil = Anvil(
    api_key=API_KEY,
    environment=ENVIRONMENT,
    endpoint_url=ENDPOINT_URL
)
```

## Testing and Development

For development and testing, AI agents can use the CLI tools:

```bash
# Test API connection
python -m python_anvil.cli current-user

# Generate PDF from markdown
python -m python_anvil.cli generate-pdf -i input.md -o output.pdf

# Fill PDF template
python -m python_anvil.cli fill-pdf -i data.json -t template_id -o filled.pdf
```

## Resources

- **API Documentation**: [Anvil API docs](https://www.useanvil.com/docs)
- **GraphQL Reference**: [GraphQL API reference](https://www.useanvil.com/docs/api/graphql/reference/)
- **Examples**: See the `examples/` directory for working code samples
- **CLI Reference**: Use `python -m python_anvil.cli --help` for command-line options

## Support

For AI agent developers:
- Check the [examples directory](./examples/) for working implementations
- Review the [test suite](./tests/) for usage patterns
- Consult the [Anvil developer documentation](https://www.useanvil.com/developers) for API details

---

*This guide is designed to help AI agents effectively integrate with Anvil's paperwork automation platform using the Python library.*
