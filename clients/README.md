# Silabs AI Client SDKs

Reusable clients for Silabs products and internal services.

## JavaScript

```js
import { SilabsAIClient } from "./clients/javascript/index.js";

const ai = new SilabsAIClient({
  baseUrl: process.env.SILABS_AI_URL,
  apiKey: process.env.SILABS_AI_KEY,
  clientId: "unixpress",
});

const result = await ai.chat({
  message: "Explain normalization in databases.",
});
console.log(result.text);
```

Streaming:

```js
for await (const item of ai.streamChat({ message: "Explain PostGIS." })) {
  if (item.event === "chunk") process.stdout.write(item.data.text);
  if (item.event === "final") console.log("\nFinal:", item.data.text);
}
```

## Python

```python
from clients.python.silabs_ai_client import SilabsAIClient

ai = SilabsAIClient(
    base_url="http://127.0.0.1:8000",
    api_key="...",
    client_id="unixpress",
)

print(ai.chat(message="Explain normalization in databases.")["text"])
```

Streaming:

```python
for item in ai.stream_chat(message="Explain PostGIS."):
    if item.event == "chunk":
        print(item.data["text"], end="", flush=True)
    elif item.event == "final":
        print("\nFinal:", item.data["text"])
```

The raw API key belongs only in the calling product's server-side secret store.
Do not expose it in browser-delivered JavaScript.
