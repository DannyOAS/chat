# DigitalOcean AI Agent Integration

This document explains how ShoshChat AI integrates with DigitalOcean AI Agents for conversational AI capabilities.

## Overview

ShoshChat uses DigitalOcean AI Agents as the primary LLM provider for generating chat responses. The integration is flexible and supports:

- Global default endpoint configuration
- Per-tenant endpoint customization via `LLMConfig` model
- Automatic fallback to OpenAI adapter if Gradient fails

## Configuration

### Environment Variables

Set the following in your `.env` file:

```bash
# AI Provider Configuration
AI_PROVIDER=gradient
DO_GRADIENT_API_KEY=your-api-key-here
DO_GRADIENT_ENDPOINT=https://your-agent-endpoint.agents.do-ai.run
```

### Current Configuration

The project is configured with:
- **Endpoint:** `https://ijszbvtt5xxsbdu2fhgtmiot.agents.do-ai.run`
- **API Key:** Stored in `.env` (never commit this!)

## How It Works

### 1. Service Layer

The `GradientLLM` service (`chatbot/services/gradient_service.py`) handles communication with the AI agent:

```python
class GradientLLM:
    def __init__(self, endpoint: str, *, timeout: int = 30, api_key: str | None = None):
        self.endpoint = endpoint
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def generate(self, message: str, **kwargs) -> str:
        # Sends request to DO AI Agent
        # Returns generated response
```

### 2. Adapter Pattern

The `GradientAdapter` (`nlp/adapters/gradient_adapter.py`) wraps the service:

```python
class GradientAdapter:
    def __init__(self, config):
        self.config = config
        self.client = GradientLLM(config.endpoint)
```

### 3. Chatbot Service

The `ChatbotService` orchestrates the entire flow:

1. Retrieves relevant knowledge chunks from the database
2. Enriches the user message with contextual information
3. Calls the Gradient adapter to generate a response
4. Falls back to OpenAI if Gradient fails
5. Logs the interaction and tracks usage

## Per-Tenant Configuration

Each tenant can have custom AI settings via the `LLMConfig` model:

```python
# Create tenant-specific configuration
LLMConfig.objects.create(
    tenant=my_tenant,
    endpoint="https://custom-agent.agents.do-ai.run",
    model_name="llama-3.3-70b-instruct",
    system_prompt="You are a helpful retail assistant...",
    temperature=0.3
)
```

### Database Schema

```sql
CREATE TABLE nlp_llmconfig (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT REFERENCES tenancy_tenant(id),
    endpoint VARCHAR(200),
    model_name VARCHAR(255),
    system_prompt TEXT,
    temperature FLOAT DEFAULT 0.3,
    UNIQUE(tenant_id, model_name)
);
```

## API Request Format

The integration sends requests in this format:

```json
{
  "inputs": [
    {
      "role": "system",
      "content": "You are a helpful assistant..."
    },
    {
      "role": "user",
      "content": "User's message with context..."
    }
  ]
}
```

Expected response:

```json
{
  "outputs": [
    {
      "content": "AI generated response..."
    }
  ]
}
```

## Testing the Integration

### 1. Unit Tests

Run the Gradient service tests:

```bash
cd shoshchat
pytest chatbot/tests/test_gradient_service.py -v
```

### 2. Manual Testing

Create a test tenant and send a chat message:

```python
# In Django shell
from chatbot.services.chatbot_service import ChatbotService
from tenancy.models import Tenant

tenant = Tenant.objects.first()
service = ChatbotService(tenant)
response = service.process_message("Hello, how are you?", "test-user-123")
print(response)
```

### 3. API Testing

```bash
# Test the chat endpoint
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are your business hours?",
    "user_id": "test-user-456"
  }'
```

## Monitoring & Debugging

### Enable Debug Logging

Add to your `.env`:

```bash
DJANGO_DEBUG=True
```

Check logs for Gradient service calls:

```bash
docker-compose logs -f web | grep gradient
```

### Common Issues

**Issue:** `RuntimeError: The requests library is required`
**Solution:** Ensure `requests` is installed: `pip install requests`

**Issue:** `ValueError: Unexpected response from Gradient API`
**Solution:** Check the endpoint URL and API key are correct

**Issue:** API returns 401 Unauthorized
**Solution:** Verify your `DO_GRADIENT_API_KEY` is valid and not expired

## Fallback Behavior

If the Gradient adapter fails, the system automatically falls back to `OpenAIAdapter`:

```python
try:
    response = adapter.generate(enriched_message)
except Exception:
    logger.exception("Falling back to OpenAI adapter")
    response = OpenAIAdapter().generate(enriched_message)
```

This ensures high availability even if the primary AI agent is unavailable.

## Security Best Practices

1. **Never commit API keys** - Always use environment variables
2. **Rotate keys regularly** - Update `DO_GRADIENT_API_KEY` periodically
3. **Use different keys per environment** - Separate dev/staging/production keys
4. **Monitor usage** - Track API calls and set up alerts for unusual patterns
5. **Implement rate limiting** - Already configured at 120 requests/min per user

## Production Checklist

- [ ] Set production API key in environment variables
- [ ] Configure production endpoint URL
- [ ] Set up monitoring and alerting
- [ ] Test failover to OpenAI adapter
- [ ] Configure appropriate timeouts (default: 30s)
- [ ] Set up log aggregation for debugging
- [ ] Implement retry logic with exponential backoff
- [ ] Monitor token usage and costs

## Advanced Configuration

### Custom Timeouts

```python
llm = GradientLLM(
    endpoint=settings.DO_GRADIENT_ENDPOINT,
    timeout=60,  # Increase for slower responses
    api_key=settings.DO_GRADIENT_API_KEY
)
```

### System Prompts

Customize per tenant:

```python
LLMConfig.objects.filter(tenant=tenant).update(
    system_prompt="""
    You are ShoshChat, an AI assistant for e-commerce.
    Always be helpful, concise, and professional.
    Use the provided business context to answer questions accurately.
    """
)
```

## Support

For issues with:
- **ShoshChat integration:** Check `DEVELOPER_GUIDE.md`
- **DigitalOcean AI Agents:** Visit DigitalOcean AI documentation
- **API errors:** Review logs and check endpoint status

---

Last updated: 2025-11-15
