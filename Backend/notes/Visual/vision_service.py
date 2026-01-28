import os
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Setup Logger
logger = logging.getLogger(__name__)

# Initialize Groq Client
try:
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
    logger.info("✅ Groq Vision Client Initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Groq Client: {e}")
    client = None

def describe_image(base64_string: str, prompt: str = "Describe this detailed scientific figure/table concisely. Focus on the key trends, data points, and structural relationships shown.") -> str:
    """
    Generate a text description for a base64 encoded image using Groq Vision model.
    """
    if not client:
        logger.error("Groq client not initialized")
        return "[Error: Vision Client Unavailable]"

    if not base64_string:
        return "[Error: Empty Image Data]"

    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": prompt
                        },
                        {
                            "type": "image_url", 
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_string}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=300,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        description = completion.choices[0].message.content
        return description.strip()

    except Exception as e:
        logger.error(f"❌ Vision API Call Failed: {e}")
        return f"[Error processing image: {str(e)}]"
