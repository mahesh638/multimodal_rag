import boto3

# Initialize the DynamoDB resource
dynamodb = boto3.resource("dynamodb", region_name="us-west-1")  # Update your region if needed

# Reference the existing table
table_name = "pdf_by_pages"
table = dynamodb.Table(table_name)

# Sample entry to insert
item = {
    "pdf_uuid": "123e4567-e89b-12d3-a456-426614174000",  # Unique identifier (partition key)
    "page_number": 1,  # Additional attribute (optional)
    "content": "This is the extracted text from page 1 of the PDF.",
    "metadata": {
        "author": "John Doe",
        "upload_date": "2025-03-21"
    }
}

# Insert into DynamoDB
response = table.put_item(Item=item)

# Print response to confirm success
print("Entry added successfully:", response)
