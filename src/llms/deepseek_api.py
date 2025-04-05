# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI, AsyncOpenAI
import json
import asyncio

from src.config import DEEPSEEK_API_KEY

# Create both sync and async clients
sync_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
async_client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


class DeepSeekApi():
    @staticmethod
    def chat(message: str, model: str = "deepseek-chat", system_prompt: str = "You are a helpful assistant"):
        """
        Synchronous version of the chat method (kept for backward compatibility)
        """
        try:
            print(f"🔄 Calling DeepSeek API with model: {model}")
            
            response = sync_client.chat.completions.create(
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
            
            if not response or not response.choices or len(response.choices) == 0:
                raise ValueError("DeepSeek API returned empty response or choices array")
            
            content = response.choices[0].message.content
            
            if content is None:
                raise ValueError("DeepSeek API returned None content")
            
            # Validate that the content is valid JSON
            try:
                # Just try to parse it to validate, we don't need to store the result here
                json.loads(content)
            except json.JSONDecodeError as e:
                print(f"⚠️ DeepSeek API returned invalid JSON: {str(e)}")
                print(f"⚠️ Response content: {content[:500]}...")  # Print first 500 chars
                raise ValueError(f"DeepSeek API returned invalid JSON: {str(e)}")
            
            return content
            
        except Exception as e:
            print(f"⚠️ DeepSeek API error: {str(e)}")
            # Re-raise the exception with more context
            raise RuntimeError(f"DeepSeek API error: {str(e)}")
    
    @staticmethod
    async def achat(message: str, model: str = "deepseek-chat", system_prompt: str = "You are a helpful assistant"):
        """
        Asynchronous version of the chat method
        
        Args:
            message: The message to send to the API
            model: The model to use
            system_prompt: The system prompt to use
        
        Returns:
            The API response content
        """
        try:
            print(f"🔄 Calling DeepSeek API asynchronously with model: {model}")
            
            response = await async_client.chat.completions.create(
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
            
            if not response or not response.choices or len(response.choices) == 0:
                raise ValueError("DeepSeek API returned empty response or choices array")
            
            content = response.choices[0].message.content
            
            if content is None:
                raise ValueError("DeepSeek API returned None content")
            
            # Validate that the content is valid JSON
            try:
                # Just try to parse it to validate, we don't need to store the result here
                json.loads(content)
            except json.JSONDecodeError as e:
                print(f"⚠️ DeepSeek API returned invalid JSON: {str(e)}")
                print(f"⚠️ Response content: {content[:500]}...")  # Print first 500 chars
                raise ValueError(f"DeepSeek API returned invalid JSON: {str(e)}")
            
            return content
            
        except Exception as e:
            print(f"⚠️ DeepSeek API error (async): {str(e)}")
            # Re-raise the exception with more context
            raise RuntimeError(f"DeepSeek API error (async): {str(e)}")
