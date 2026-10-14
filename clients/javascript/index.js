export class SilabsAIClient {
  constructor({ baseUrl, apiKey, clientId, fetchImpl = fetch }) {
    if (!baseUrl) throw new Error("baseUrl is required");
    if (!apiKey) throw new Error("apiKey is required");
    if (!clientId) throw new Error("clientId is required");
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
    this.clientId = clientId;
    this.fetch = fetchImpl;
  }

  _headers(extra = {}) {
    return {
      "Content-Type": "application/json",
      "X-Silabs-Client": this.clientId,
      "X-Silabs-API-Key": this.apiKey,
      ...extra,
    };
  }

  async _json(path, options = {}) {
    const response = await this.fetch(this.baseUrl + path, {
      ...options,
      headers: this._headers(options.headers),
    });
    const requestId = response.headers.get("X-Request-ID");
    let payload = null;
    try {
      payload = await response.json();
    } catch {
      payload = {};
    }
    if (!response.ok) {
      const error = new Error(payload?.detail || `Silabs AI request failed: ${response.status}`);
      error.status = response.status;
      error.requestId = requestId;
      throw error;
    }
    if (payload && requestId && !payload.request_id) {
      payload.request_id = requestId;
    }
    return payload;
  }

  chat(payload) {
    return this._json("/v1/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  generate(payload) {
    return this._json("/v1/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  usage() {
    return this._json("/v1/usage", { method: "GET" });
  }

  health() {
    return this._json("/v1/health", { method: "GET" });
  }

  async *streamChat(payload) {
    const response = await this.fetch(this.baseUrl + "/v1/chat/stream", {
      method: "POST",
      headers: this._headers({ Accept: "text/event-stream" }),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let detail = `Silabs AI stream failed: ${response.status}`;
      try {
        const data = await response.json();
        detail = data?.detail || detail;
      } catch {}
      const error = new Error(detail);
      error.status = response.status;
      error.requestId = response.headers.get("X-Request-ID");
      throw error;
    }

    if (!response.body) throw new Error("Streaming response body is unavailable");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let boundary;
      while ((boundary = buffer.indexOf("\n\n")) !== -1) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const lines = block.split("\n");
        let event = "message";
        let data = "";
        for (const line of lines) {
          if (line.startsWith("event:")) event = line.slice(6).trim();
          if (line.startsWith("data:")) data += line.slice(5).trim();
        }
        if (!data) continue;
        yield { event, data: JSON.parse(data) };
      }
    }
  }
}
