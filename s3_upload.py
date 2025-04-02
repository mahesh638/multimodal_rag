import boto3

# Initialize the S3 client
s3 = boto3.client("s3", region_name="us-west-1")  # Update with your correct region

# Define bucket name and file details
bucket_name = "my-rag-images"
file_path = "doc.pdf"  # Local file path
s3_key = "uploads/doc.pdf"  # Path inside S3 bucket

# Upload the file to S3
try:
    s3.upload_file(file_path, bucket_name, s3_key)
    print(f"✅ File '{file_path}' uploaded successfully to S3 bucket '{bucket_name}' at '{s3_key}'")
except Exception as e:
    print(f"❌ Error uploading file: {e}")
