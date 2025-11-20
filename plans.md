Backend API -> Python FastAPI. To handle chat requests

AI Model -> OpenAI key/GPT Model

React -> User chat interface

Language Translation -> Google Translation API or DeepL API. For swahili + english

Database -> SQLite/supabase. save chat history

Deployment -> Vercel. Hosting

Converstion flows

Detect language of the user message (Swahili or English).

Translate to English if needed (for GPT processing).

Query the GPT model with relevant context (laws, survey data, etc.).

Translate the answer back to Swahili if the original input was in Swahili.

Display the response in a friendly chat UI.