from src.llm.client import generate_response


prompt = """
Explain in one sentence what warm minimalism means in interior design.
"""


response = generate_response(prompt)

print(response)