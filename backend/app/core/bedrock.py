"""Amazon Bedrock client — generates text embeddings via Titan Embeddings."""
import json
import boto3
from app.config import settings

_bedrock_client = None


def get_bedrock_client():
    global _bedrock_client
    if not _bedrock_client:
        _bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.AWS_REGION,
        )
    return _bedrock_client


async def generate_embedding(text: str) -> list[float] | None:
    """
    Calls Bedrock Titan Embeddings and returns a 1536-dim vector.
    Returns None if Bedrock is unavailable (e.g. local dev without AWS credentials).
    """
    try:
        client = get_bedrock_client()
        body = json.dumps({"inputText": text[:8000]})  # Titan max input is 8192 tokens
        response = client.invoke_model(
            modelId=settings.BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        result = json.loads(response["body"].read())
        return result["embedding"]  # list of 1536 floats
    except Exception:
        return None  # graceful fallback — similarity search skips silently
