# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI

from src.config import DEEPSEEK_API_KEY

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


class DeepSeekApi():
    @staticmethod
    def chat(message: str, model: str = "deepseek-chat", system_prompt: str = "You are a helpful assistant"):
        response = client.chat.completions.create(
            model=model,
            temperature=0.4,
            response_format={
                'type': 'json_object'
            },
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            stream=False
        )
        return response.choices[0].message.content
