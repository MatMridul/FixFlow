import os

# The app wires a real Gemini -> Mistral chain whenever keys exist in .env.
# Tests must stay offline, deterministic and free of quota spend.
os.environ["FIXFLOW_DISABLE_LLM"] = "1"
