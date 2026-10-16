# Architecture

## Runtime

```text
Tauri + React desktop UI
        |
        v
Local Humanizer service
        |
        +--> document parser
        +--> preservation engine
        +--> rewrite pipeline
        +--> critic
        +--> style profile
        |
        v
Silabs AI local model runtime
        |
        v
Qwen3-1.7B (target: 4-bit GGUF)
```

## Processing flow

```text
Document
  -> parse structure
  -> split into logical blocks
  -> protect citations/numbers/URLs/etc.
  -> rewrite
  -> critic review
  -> optional revision
  -> restore protected values
  -> validate preservation
  -> present diff
  -> user accepts/rejects
```

## Design rules

1. Offline first. Document content must not leave the device.
2. Preserve meaning and protected facts.
3. Rewrite logical blocks instead of whole long documents at once.
4. Treat model output as a proposed edit, never as an unquestioned replacement.
5. Keep the shared Silabs AI engine separate from product-specific Humanizer logic.
