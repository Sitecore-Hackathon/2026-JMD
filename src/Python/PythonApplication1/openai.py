# -*- coding: utf-8 -*-
"""
OpenAI Engagement Checker Module

Evaluates text engagement quality using OpenAI API with fallback to heuristic scoring.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import textstat
except ImportError:
    textstat = None

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

load_dotenv()  # Load from .env file


class OpenAIEngagementChecker:
    """
    Evaluate engagement quality of text using OpenAI API.

    Features:
    - Uses the modern OpenAI SDK (openai.OpenAI client)
    - Reads API key from OPENAI_API_KEY environment variable
    - Returns JSON response with fields: score (0-100), label, reasons, suggestions
    - Falls back to lightweight heuristic if OpenAI is unavailable
    - Graceful error handling with detailed logging
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the OpenAI Engagement Checker.
        
        Args:
            api_key: Optional API key. If not provided, reads from OPENAI_API_KEY env var.
            model: The OpenAI model to use (default: gpt-4o-mini for cost-efficiency).
        """
        # Check if OpenAI SDK is installed
        if OpenAI is None:
            LOG.warning("OpenAI SDK not installed; falling back to heuristic scoring.")
            self.client = None
        else:
            # Get API key from parameter or environment variable (DO NOT hardcode)
            api_key =  api_key or os.getenv("OPENAI_API_KEY")
            
            if api_key:
                try:
                    # Remove any whitespace from the API key
                    api_key = api_key.strip()
                    
                    # Validate API key format
                    if not api_key.startswith("sk-"):
                        LOG.warning(
                            f"API key does not start with 'sk-'. "
                            f"Make sure you've set the correct OPENAI_API_KEY environment variable."
                        )
                    
                    self.client = OpenAI(api_key=api_key)
                    LOG.info(f"✓ OpenAI client initialized successfully with model: {model}")
                except Exception as e:
                    LOG.warning(f"Failed to initialize OpenAI client: {e}. Falling back to heuristic.")
                    self.client = None
            else:
                LOG.warning(
                    "OPENAI_API_KEY not found in environment. Falling back to heuristic scoring.\n"
                    "To use OpenAI: set OPENAI_API_KEY environment variable."
                )
                self.client = None
        
        self.model = model

    def _build_prompt(self, text: str) -> str:
        """Build the prompt for OpenAI to evaluate engagement."""
        return (
            "You are an expert engagement analyst evaluating text for reader engagement quality. "
            "Return ONLY a single valid JSON object (no markdown, no surrounding text) with these exact fields:\n"
            "- score: integer between 0 and 100 (100 = extremely engaging, 0 = not engaging at all)\n"
            "- label: one of ['Very Low', 'Low', 'Medium', 'High', 'Very High']\n"
            "- reasons: array of 2-3 short strings explaining why this score was given\n"
            "- suggestions: array of 2-3 short actionable suggestions to improve engagement\n\n"
            "Consider elements such as:\n"
            "- Clarity: Is the message clear and easy to understand?\n"
            "- Emotional appeal: Does it trigger emotional responses?\n"
            "- Active voice: Does it use active, compelling language?\n"
            "- Concrete examples: Are there specific examples or evidence?\n"
            "- Brevity: Is it concise yet impactful?\n"
            "- Audience relevance: How relevant is it to the target audience?\n"
            "- Call-to-action: Is there a clear, compelling next step?\n\n"
            "If the input is empty or not valid text, return score 0 with appropriate label/reasons.\n\n"
            "Text to evaluate:\n"
            f"{text}"
        )

    def _map_score_to_label(self, score: int) -> str:
        """Map a numeric score to a categorical engagement label."""
        if score < 20:
            return "Very Low"
        elif score < 40:
            return "Low"
        elif score < 60:
            return "Medium"
        elif score < 80:
            return "High"
        else:
            return "Very High"

    def _heuristic_engagement(self, text: str) -> Dict[str, Any]:
        """
        Lightweight fallback engagement scoring when OpenAI is unavailable.
        
        Uses text length and readability metrics to estimate engagement.
        """
        if not text or not text.strip():
            return {
                "score": 0,
                "label": "Very Low",
                "reasons": ["Empty or whitespace-only text"],
                "suggestions": ["Provide meaningful, substantive content"]
            }

        # Calculate text metrics
        word_count = len(text.split())
        try:
            flesch = textstat.flesch_reading_ease(text) if textstat else 50.0
        except Exception:
            flesch = 50.0

        # Heuristic scoring: ideal length is ~100-150 words, higher readability is better
        length_factor = max(0, 1 - abs(word_count - 120) / 200)
        readability_factor = 0.6 + 0.4 * (flesch / 100)
        score = int(max(0, min(100, length_factor * readability_factor * 100)))
        label = self._map_score_to_label(score)

        reasons = []
        suggestions = []
        
        # Provide feedback on length
        if word_count < 20:
            reasons.append("Very short - may lack depth and context")
            suggestions.append("Expand with concrete examples or supporting details")
        elif word_count > 500:
            reasons.append("Very long - may lose reader attention")
            suggestions.append("Break into shorter sections with clear headings")
        else:
            reasons.append(f"Good length ({word_count} words) for engagement")

        # Provide feedback on readability
        if flesch < 50:
            reasons.append("Low readability - complex sentences or vocabulary")
            suggestions.append("Simplify sentences and use everyday language")
        else:
            reasons.append("Good readability - clear and accessible language")

        return {
            "score": score,
            "label": label,
            "reasons": reasons,
            "suggestions": suggestions
        }

    def check_engagement(self, text: str, timeout: int = 15) -> Dict[str, Any]:
        """
        Evaluate the engagement quality of the provided text.
        
        Uses OpenAI if available and configured; otherwise uses heuristic scoring.
        
        Args:
            text: The text to evaluate for engagement
            timeout: Request timeout in seconds (default: 15)
        
        Returns:
            A dictionary with keys: score, label, reasons, suggestions
        """
        # If text is empty, return early
        if not text or not text.strip():
            return self._heuristic_engagement(text)

        # If OpenAI client is not available, use heuristic
        if self.client is None:
            LOG.info("Using heuristic engagement scoring (OpenAI unavailable)")
            return self._heuristic_engagement(text)

        # Try to use OpenAI API
        prompt = self._build_prompt(text)
        try:
            LOG.info(f"Sending engagement evaluation request to OpenAI (text length: {len(text)} chars)")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON-only response assistant. Return only valid JSON, no markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=400,
                temperature=0.3,
            )
            
            content = response.choices[0].message.content.strip()
            LOG.debug(f"Received response from OpenAI: {content[:100]}...")
            
            # Extract JSON from response (handle potential markdown wrapping)
            first_brace = content.find("{")
            last_brace = content.rfind("}")
            
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_text = content[first_brace:last_brace + 1]
            else:
                json_text = content

            # Parse and validate JSON response
            data = json.loads(json_text)
            
            # Normalize and validate result
            score = int(data.get("score", 0))
            score = max(0, min(100, score))
            label = data.get("label", self._map_score_to_label(score))
            reasons = data.get("reasons", [])
            suggestions = data.get("suggestions", [])
            
            LOG.info(f"✓ OpenAI evaluation complete: score={score}, label={label}")
            return {
                "score": score,
                "label": label,
                "reasons": reasons,
                "suggestions": suggestions
            }
            
        except json.JSONDecodeError as e:
            LOG.warning(f"Failed to parse JSON from OpenAI response: {e}. Falling back to heuristic.")
            return self._heuristic_engagement(text)
        except Exception as exc:
            LOG.warning(f"OpenAI call failed: {exc}. Falling back to heuristic.")
            return self._heuristic_engagement(text)


if __name__ == "__main__":
    import sys

    # Initialize checker (will use OpenAI if available, otherwise heuristic)
    checker = OpenAIEngagementChecker()
    
    # Get text from command-line argument or stdin
    if len(sys.argv) >= 2:
        text = sys.argv[1]
    else:
        LOG.info("No argument provided; reading from stdin. End input with EOF (Ctrl+D / Ctrl+Z).")
        text = sys.stdin.read()

    # Evaluate and output results
    result = checker.check_engagement(text)
    print("\n" + "="*70)
    print("ENGAGEMENT EVALUATION RESULT")
    print("="*70)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("="*70 + "\n")