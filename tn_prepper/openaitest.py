from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
  model="o1-preview",
  messages=[
    {"role": "user", "content": "What roles can I use in a chat completion as of today?"},

  ]
)

print(completion.choices[0].message)
