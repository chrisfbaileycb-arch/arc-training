# Offline Client Wiring — one local endpoint: http://localhost:8080/v1

- Hey Buddy: docs/HEY-BUDDY-INTEGRATION.md (OpenAI-compatible provider + agent scope).
- LM Studio: My Models -> add local .gguf from the drive. Fully offline.
- Jan: Settings -> Model Providers -> Local -> import .gguf from the drive.
- VS Code: Continue/Cline -> "OpenAI Compatible" -> Base URL http://localhost:8080/v1,
  key EMPTY, model = .gguf filename.
- Coding CLIs: export OPENAI_BASE_URL=http://localhost:8080/v1 ; export OPENAI_API_KEY=EMPTY
- Verification habit: disable Wi-Fi and ask for a function. Answers = real.
