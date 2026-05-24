# Module 09: AI Interview (Astra)

## Architecture (AI vs OSS)

| Capability | Implementation |
|------------|----------------|
| JD / resume parse (PDF, DOCX) | Django `document_parser.py` — no AI |
| Resume–JD match | Django `matching.py` — OSS embeddings + skills |
| Hindi → English | Django `translation.py` — Argos Translate |
| Voice answer score | Django `answer_scoring.py` — OSS embeddings |
| HR report | Django `report_builder.py` — template |
| Interview questions + ideal answers | ai-service — **gpt-5.4-mini** |
| MCQ assessment generation | ai-service — **gpt-5.4-mini** |
| STT | ai-service — OpenAI `whisper-1` |
| TTS (Astra) | ai-service — OpenAI `tts-1` |

## Backend Models

- `AiInterviewSession`, `AiInterviewQuestion`, `AiInterviewReport`
- `AssessmentTemplate`, `AssessmentQuestion`, `AssessmentAttempt`, `ProctorSnapshot`

## API Endpoints

- `POST /api/v1/recruitment/candidates/` (multipart resume, PDF/DOCX only)
- `POST /api/v1/recruitment/candidates/{id}/match/` (local OSS)
- Public ai-service: `generate-questions`, `generate-assessment`, `transcribe`, `tts`

## Frontend Routes

- HR: `/recruitment/candidates/new`, `/recruitment/ai-scores`, `/recruitment/ai-interviews`, `/recruitment/assessments`
- Candidate: `/interview/join/[token]`, `/interview/[sessionId]/live`, `/assessment/[token]`
