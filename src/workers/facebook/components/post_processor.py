"""Post processing utilities for Facebook scraper."""

import json
from src.llms.deepseek_api import DeepSeekApi


async def process_posts_batch(posts_data: list) -> list:
    """
    Process a batch of post texts and extract apartment data using DeepSeek API
    
    Args:
        posts_data: List of post texts to process
    
    Returns:
        List of processed post data
    """
    system_prompt = (
        "You are an intelligent text analyzer and HTML parser that extracts key data from Facebook posts. "
        "I will provide you with an array of Facebook post texts from apartment rental groups. "
        "Your job is to analyze each text and return an array of structured JSON objects IN THE SAME ORDER as the input array. "
        "The length of your output array must match the length of the input array. "
        "For each post text in the input array, extract the following information as a JSON object:\n\n"
        "1. user: The full name of the user who posted.\n"
        "2. timestamp: The date and time the post was uploaded.\n"
        "3. post_link: A direct permalink to the post if available.\n"
        "4. text: The full human-readable content of the post shuold be same content more orgnaized (ignore layout, comments, ads, etc.).\n"
        "6. price: The rent price or total cost if mentioned (in NIS).\n"
        "7. location: The location of the apartment if mentioned.\n"
        "8. phone_numbers: An array of phone numbers in the post (e.g. 05XXXXXXXX).\n"
        "9. images: An array of image URLs that are part of the post content (exclude icons and irrelevant assets).\n"
        "10. mentions: List of specific words or keywords like 'סאבלט', 'שכירות', etc.\n"
        "11. summary: A brief natural language summary(in Hebrew) of the post intent or offer.\n"
        "12. is_valid: A boolean value indicating if the post is a valid apartment post which meant that the user is offering an apartment (true) or not (false).\n"
        "Return ONLY a valid JSON array containing one object for each input text, in the same order. "
        "If any field cannot be found, set it to null or empty string/array.\n"
        "IMPORTANT: The output MUST be a JSON array with the same number of objects as the input array, in the same order named as output.\n"
    )
    
    # Convert list of post texts to JSON string
    posts_json = json.dumps(posts_data, ensure_ascii=False)
    
    try:
        # Print a sample of the input data for debugging
        post_sample = posts_data[0][:100] if posts_data and len(posts_data) > 0 else "Empty"
        print(f"📤 Input sample: {post_sample}...")
        
        # Use the async version of the DeepSeek API
        response = await DeepSeekApi.achat(
            posts_json, 
            system_prompt=system_prompt
        )
        
        if response is None:
            raise RuntimeError("DeepSeek API returned None")
        
        # Print the raw response for debugging
        print(f"🔍 DeepSeek API raw response: {response[:200]}...") # Show first 200 chars
        
        # Parse the JSON response
        parsed_response = json.loads(response)
        
        # Check the response structure and extract the actual data
        result = None
        
        if isinstance(parsed_response, dict):
            # Try common patterns in response structure
            if 'output' in parsed_response:
                result = parsed_response['output']
        elif isinstance(parsed_response, list):
            # If the response is already a list, use it directly
            result = parsed_response
        else:
            raise ValueError(f"Expected dict or list, but got {type(parsed_response).__name__}")
        
        # Validate the result is a list
        if not isinstance(result, list):
            if result is None:
                raise ValueError("Result is None")
            else:
                # Try to convert to list if possible
                print(f"⚠️ Result is not a list, attempting to convert. Type: {type(result).__name__}")
                try:
                    if isinstance(result, dict):
                        # If it's a single object, wrap it in a list
                        result = [result]
                    else:
                        result = list(result)
                except:
                    raise ValueError(f"Could not convert result to list. Type: {type(result).__name__}")
        
        # Check if the result has the expected length
        if len(result) != len(posts_data):
            print(f"⚠️ Result length mismatch: got {len(result)}, expected {len(posts_data)}")
            # If too few results, pad with empty objects
            if len(result) < len(posts_data):
                print("⚠️ Padding result with empty objects")
                empty_obj = {
                    "user": "",
                    "timestamp": "",
                    "post_link": "",
                    "text": "",
                    "price": None,
                    "location": "",
                    "phone_numbers": [],
                    "images": [],
                    "mentions": [],
                    "summary": "",
                    "is_valid": False
                }
                result.extend([empty_obj] * (len(posts_data) - len(result)))
            # If too many results, truncate
            elif len(result) > len(posts_data):
                print("⚠️ Truncating result to match input length")
                result = result[:len(posts_data)]
        
        return result
    
    except json.JSONDecodeError as e:
        # Handle JSON parsing errors
        error_message = f"Failed to parse API response as JSON: {e}."
        if response is not None:
            error_message += f" Response: {response[:500]}"
        raise ValueError(error_message)
    except Exception as e:
        # Handle other errors
        error_message = f"Error processing batch: {e}."
        if response is not None:
            error_message += f" Response type: {type(response)}, content: {str(response)[:500]}"
        raise RuntimeError(error_message) 