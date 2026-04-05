# AI Backend Setup

Clippings supports any OpenAI-compatible AI backend. Choose the one that fits your setup.

## Ollama

The easiest local option.

1. Install [Ollama](https://ollama.com)
2. Pull a model:
   ```bash
   ollama pull llama3.1
   ```
3. Configure:
   ```yaml
   ai:
     provider: ollama
     base_url: http://localhost:11434
     model: llama3.1
   ```

If Ollama runs on a different machine, use its IP:
```yaml
base_url: http://192.168.1.100:11434
```

## llama.cpp (Server Mode)

Run GGUF models directly with llama.cpp's built-in server.

1. Start the server:
   ```bash
   ./llama-server -m /path/to/model.gguf --port 8080
   ```
2. Configure:
   ```yaml
   ai:
     provider: openai-compatible
     base_url: http://localhost:8080/v1
     model: default
   ```

The model name must be `default` — that's what llama.cpp's server uses.

## OpenAI

```yaml
ai:
  provider: openai
  model: gpt-4o
  api_key: "sk-..."
```

Leave `base_url` empty to use OpenAI's default endpoint.

## Anthropic

```yaml
ai:
  provider: anthropic
  model: claude-sonnet-4-20250514
  api_key: "sk-ant-..."
```

## Any OpenAI-Compatible Endpoint

Works with vLLM, Tabby, LM Studio, etc.

```yaml
ai:
  provider: openai-compatible
  base_url: http://your-server:8000/v1
  model: your-model-name
  api_key: ""   # or your API key if required
```

## Model Recommendations

For local summarization (32GB RAM):

| Model | Quant | RAM | Speed |
|---|---|---|---|
| Qwen2.5-32B | Q4_K_M | ~19GB | ~3-5 tok/s |
| Mistral Small 24B | Q4_K_M | ~14GB | ~6-8 tok/s |
| Llama-3.1-8B | Q6_K | ~6GB | ~15-20 tok/s |
