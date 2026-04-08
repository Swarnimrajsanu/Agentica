import httpx
from loguru import logger
from config.settings import settings
from typing import Optional


class LLMService:
    """OpenRouter LLM Service for AI model interactions."""
    
    def __init__(self):
        self.base_url = settings.OPENROUTER_BASE_URL
        self.api_key = settings.OPENROUTER_API_KEY
        self.default_model = settings.DEFAULT_MODEL
        logger.info("LLM Service initialized with OpenRouter")
    
    async def call_llm(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Optional[str]:
        """
        Call LLM model via OpenRouter API.
        
        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt
            model: Model to use (defaults to settings.DEFAULT_MODEL)
            temperature: Temperature for response generation (0.0-1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            LLM response text or None if error
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://agentica.app",
            "X-Title": "Agentica"
        }
        
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add user message
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    logger.info(f"LLM response received ({len(content)} chars)")
                    return content
                else:
                    logger.error(f"LLM API error: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("LLM API request timed out")
            return None
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return None
    
    async def call_llm_with_context(
        self,
        prompt: str,
        context: str,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Call LLM with additional context.
        
        Args:
            prompt: User prompt
            context: Additional context information
            model: Model to use
            temperature: Temperature for response
            
        Returns:
            LLM response text
        """
        system_prompt = f"""You are an AI assistant with the following context:

{context}

Please use this context to inform your responses."""
        
        return await self.call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature
        )
    
    async def generate_embeddings(self, text: str, model: str = "text-embedding-3-small") -> Optional[list]:
        """
        Generate embeddings for text.
        
        Args:
            text: Text to embed
            model: Embedding model to use
            
        Returns:
            Embedding vector or None if error
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "input": text
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embeddings = result["data"][0]["embedding"]
                    logger.info(f"Embeddings generated (dim: {len(embeddings)})")
                    return embeddings
                else:
                    logger.error(f"Embeddings API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None


# Global LLM service instance
llm_service = LLMService()