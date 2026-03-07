# -*- coding: utf-8 -*-
"""
Engagement Score Checker Module

Evaluates visitor engagement quality of text content using OpenAI.
Supports checking individual strings separately using OpenAI API.
"""
import os
import json
import logging
import sys
from typing import Optional, Dict, Any


try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class OpenAIEngagementChecker:
    """
    Evaluates visitor engagement quality using OpenAI API.

    Features:
    - Uses OpenAI SDK with gpt-4o-mini model for accurate engagement scoring
    - Evaluates individual text strings independently
    - Provides detailed engagement metrics: score, label, reasons, and improvement suggestions
    - Graceful error handling with clear logging
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the engagement checker with OpenAI client.
        
        Args:
            api_key: Optional API key. If not provided, reads from OPENAI_API_KEY env var.
            model: The OpenAI model to use (default: gpt-4o-mini for cost-efficiency).
        
        Raises:
            RuntimeError: If OpenAI SDK is not installed or API key is not found.
        """
        # Check if OpenAI SDK is installed
        if OpenAI is None:
            raise RuntimeError(
                "OpenAI SDK not installed. Install it with: pip install openai"
            )
        
        # Get API key from parameter, environment variable, or raise error
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        
        # Validate API key is present
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is not set.\n"
                "Please set your OpenAI API key before running this script.\n"
                "See setup instructions in the main() function docstring."
            )
        
        # Validate API key format
        if not isinstance(self.api_key, str) or len(self.api_key.strip()) == 0:
            raise RuntimeError("OPENAI_API_KEY is empty or invalid format.")
        
        # Remove any whitespace from the API key
        self.api_key = self.api_key.strip()
        
        # Warn if key doesn't start with expected prefix
        if not self.api_key.startswith("sk-"):
            LOG.warning(
                f"API key does not start with 'sk-'. "
                f"Make sure you've set the correct OPENAI_API_KEY environment variable."
            )
        
        self.model = model
        
        # Initialize OpenAI client
        try:
            LOG.info(f"Initializing OpenAI client with model: {self.model}")
            self.client = OpenAI(api_key=self.api_key)
            LOG.info("✓ OpenAI client initialized successfully")
        except Exception as e:
            error_msg = (
                f"Failed to initialize OpenAI client: {e}\n"
                f"Possible causes:\n"
                f"  1. Invalid or expired API key\n"
                f"  2. Network connectivity issue\n"
                f"  3. OpenAI API service is down\n"
                f"  4. Wrong API key format\n"
                f"Solution: Verify your OPENAI_API_KEY is correct and active"
            )
            LOG.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _build_engagement_prompt(self, text: str) -> str:
        """
        Build a detailed prompt for OpenAI to evaluate visitor engagement.
        
        Args:
            text: The content to evaluate for engagement.
        
        Returns:
            A formatted prompt string for the OpenAI API.
        """
        return (
            "You are an expert digital marketing and content engagement analyst.\n\n"
            "Evaluate the following content for VISITOR ENGAGEMENT quality.\n"
            "Consider all factors that make content compelling, persuasive, and engaging to readers:\n\n"
            "Evaluation Criteria:\n"
            "1. Clarity: Is the message clear and easy to understand?\n"
            "2. Emotional Appeal: Does it trigger emotional responses (curiosity, urgency, trust)?\n"
            "3. Active Voice & Action: Does it use active language and compelling calls-to-action?\n"
            "4. Relevance: How relevant is the content to the target audience?\n"
            "5. Persuasiveness: Does it convince the reader to take action?\n"
            "6. Structure: Is it well-organized and easy to scan?\n"
            "7. Conciseness: Is it concise yet impactful?\n\n"
            "Return ONLY a valid JSON object (no markdown, no extra text) with exactly these fields:\n"
            "{\n"
            '  "overall_engagement_score": <integer 0-100>,\n'
            '  "engagement_label": <one of: "Very Low", "Low", "Medium", "High", "Very High">,\n'
            '  "clarity_score": <integer 0-100>,\n'
            '  "emotional_appeal_score": <integer 0-100>,\n'
            '  "persuasiveness_score": <integer 0-100>,\n'
            '  "call_to_action_strength": <integer 0-100>,\n'
            '  "structure_quality_score": <integer 0-100>,\n'
            '  "reasons": <array of 2-3 strings explaining the overall score>,\n'
            '  "strengths": <array of 2-3 strings highlighting what works well>,\n'
            '  "improvement_suggestions": <array of 3 specific, actionable suggestions to boost engagement>\n'
            "}\n\n"
            "Content to evaluate:\n"
            f"---\n{text}\n---"
        )

    def _map_score_to_label(self, score: int) -> str:
        """Map a numeric engagement score to a categorical label."""
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

    def _validate_and_normalize_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize the OpenAI response to ensure all fields are present.
        
        Args:
            data: The parsed JSON response from OpenAI.
        
        Returns:
            A normalized engagement evaluation dictionary.
        """
        # Ensure overall score is within bounds
        overall_score = int(data.get("overall_engagement_score", 0))
        overall_score = max(0, min(100, overall_score))
        
        # Normalize individual scores
        clarity = max(0, min(100, int(data.get("clarity_score", overall_score))))
        emotional = max(0, min(100, int(data.get("emotional_appeal_score", overall_score))))
        persuasiveness = max(0, min(100, int(data.get("persuasiveness_score", overall_score))))
        cta_strength = max(0, min(100, int(data.get("call_to_action_strength", overall_score))))
        structure = max(0, min(100, int(data.get("structure_quality_score", overall_score))))
        
        label = data.get("engagement_label", self._map_score_to_label(overall_score))
        
        return {
            "overall_engagement_score": overall_score,
            "engagement_label": label,
            "detailed_scores": {
                "clarity": clarity,
                "emotional_appeal": emotional,
                "persuasiveness": persuasiveness,
                "call_to_action_strength": cta_strength,
                "structure_quality": structure
            },
            "reasons": data.get("reasons", []),
            "strengths": data.get("strengths", []),
            "improvement_suggestions": data.get("improvement_suggestions", [])
        }

    def check_engagement(self, text: str) -> Dict[str, Any]:
        """
        Evaluate the visitor engagement quality of a single text string.
        
        Sends the text to OpenAI API and receives a comprehensive engagement analysis.
        
        Args:
            text: The content to evaluate for visitor engagement.
        
        Returns:
            A dictionary containing:
            - overall_engagement_score: 0-100 overall engagement rating
            - engagement_label: Categorical label (Very Low to Very High)
            - detailed_scores: Individual component scores (clarity, emotional appeal, etc.)
            - reasons: Why the score was assigned
            - strengths: What's working well in the content
            - improvement_suggestions: Specific actionable improvements
        
        Raises:
            ValueError: If the text is empty or if JSON parsing fails.
            RuntimeError: If the OpenAI API request fails.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty or whitespace-only.")
        
        prompt = self._build_engagement_prompt(text)
        
        try:
            LOG.info(f"Sending engagement evaluation request to OpenAI (text length: {len(text)} chars)")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON-only response assistant. Return only valid JSON, no markdown or extra text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=600,
                temperature=0.3,  # Lower temperature for consistent, reliable scoring
            )
            
            content = response.choices[0].message.content.strip()
            LOG.debug(f"Received response from OpenAI: {content[:100]}...")
            
            # Extract JSON from response (handle potential markdown wrapping)
            first_brace = content.find("{")
            last_brace = content.rfind("}")
            
            if first_brace == -1 or last_brace <= first_brace:
                raise ValueError(f"No valid JSON found in response: {content}")
            
            json_text = content[first_brace:last_brace + 1]
            data = json.loads(json_text)
            
            # Validate and normalize the response
            result = self._validate_and_normalize_response(data)
            
            LOG.info(
                f"✓ Engagement evaluation complete: score={result['overall_engagement_score']}, "
                f"label={result['engagement_label']}"
            )
            return result
            
        except json.JSONDecodeError as e:
            LOG.error(f"Failed to parse JSON from OpenAI response: {e}")
            raise ValueError(f"Invalid JSON in OpenAI response: {e}") from e
        except Exception as e:
            LOG.exception(f"OpenAI API request failed: {e}")
            raise RuntimeError(f"Failed to evaluate engagement: {e}") from e

    def check_individual_engagement(self, s1: str, s2: str) -> Dict[str, Any]:
        """
        Evaluate visitor engagement for two text strings INDIVIDUALLY.
        
        Each string is evaluated separately and independently using OpenAI.
        No comparison is made between the strings; results are presented separately.
        
        Args:
            s1: First text content to evaluate.
            s2: Second text content to evaluate.
        
        Returns:
            A dictionary with structure:
            {
                "first_string": {
                    "content_info": {
                        "preview": "...",
                        "length": <chars>,
                        "word_count": <words>
                    },
                    "engagement_evaluation": { ... detailed scores and analysis ... }
                },
                "second_string": {
                    "content_info": {
                        "preview": "...",
                        "length": <chars>,
                        "word_count": <words>
                    },
                    "engagement_evaluation": { ... detailed scores and analysis ... }
                },
                "evaluation_timestamp": "<ISO timestamp>"
            }
        
        Raises:
            ValueError: If either string is empty.
            RuntimeError: If OpenAI API requests fail.
        """
        if not s1 or not s1.strip():
            raise ValueError("First string cannot be empty or whitespace-only.")
        if not s2 or not s2.strip():
            raise ValueError("Second string cannot be empty or whitespace-only.")
        
        LOG.info("="*70)
        LOG.info("EVALUATING INDIVIDUAL ENGAGEMENT SCORES")
        LOG.info("="*70)
        
        # Evaluate first string
        LOG.info("Evaluating FIRST string for visitor engagement...")
        first_engagement = self.check_engagement(s1)
        
        # Evaluate second string
        LOG.info("Evaluating SECOND string for visitor engagement...")
        second_engagement = self.check_engagement(s2)
        
        # Get current timestamp
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        result = {
            "first_string": {
                "content_info": {
                    "preview": s1[:100] + "..." if len(s1) > 100 else s1,
                    "length_characters": len(s1),
                    "word_count": len(s1.split())
                },
                "engagement_evaluation": first_engagement
            },
            "second_string": {
                "content_info": {
                    "preview": s2[:100] + "..." if len(s2) > 100 else s2,
                    "length_characters": len(s2),
                    "word_count": len(s2.split())
                },
                "engagement_evaluation": second_engagement
            },
            "evaluation_timestamp": timestamp
        }
        
        LOG.info("✓ Individual engagement evaluation complete.")
        return result


def main():
    """
    CLI entry point for evaluating visitor engagement of text strings.
    
    Usage:
        # Evaluate two strings individually:
        python score.py "First piece of content" "Second piece of content"
        
        # Evaluate a single string:
        python score.py "Your content here"
        
        # Read from stdin:
        python score.py
    
    Environment Setup:
        You MUST set the OPENAI_API_KEY environment variable before running this script.
        
        1. Get your API key from https://platform.openai.com/api-keys
        
        2. Set the environment variable:
           
           Windows (Command Prompt):
               set OPENAI_API_KEY=sk-proj-your-actual-api-key
           
           Windows (PowerShell):
               $env:OPENAI_API_KEY='sk-proj-your-actual-api-key'
           
           macOS/Linux (Bash):
               export OPENAI_API_KEY='sk-proj-your-actual-api-key'
           
           macOS/Linux (Zsh):
               export OPENAI_API_KEY='sk-proj-your-actual-api-key'
        
        3. Verify the key is set:
           
           Windows:
               echo %OPENAI_API_KEY%
           
           macOS/Linux:
               echo $OPENAI_API_KEY
        
        4. Run your script:
           
           python score.py "Your text here"
    """
    try:
        print("\n" + "="*70)
        print("INITIALIZING OPENAI ENGAGEMENT CHECKER")
        print("="*70)
        
        checker = OpenAIEngagementChecker()
        
        print("="*70 + "\n")
        
        if len(sys.argv) >= 3:
            # Two strings provided: evaluate individually
            s1 = sys.argv[1]
            s2 = sys.argv[2]
            LOG.info("Mode: Individual evaluation of two strings")
            result = checker.check_individual_engagement(s1, s2)
            
        elif len(sys.argv) == 2:
            # Single string provided
            text = sys.argv[1]
            LOG.info("Mode: Individual evaluation of single string")
            result = checker.check_engagement(text)
            
        else:
            # Read from stdin
            LOG.info("No arguments provided. Reading from stdin (press Ctrl+D or Ctrl+Z to end):")
            text = sys.stdin.read()
            if not text.strip():
                print("Error: No input provided.", file=sys.stderr)
                return 1
            result = checker.check_engagement(text)
        
        # Display results
        print("\n" + "="*70)
        print("VISITOR ENGAGEMENT SCORE RESULTS")
        print("="*70)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("="*70 + "\n")
        return 0
        
    except RuntimeError as e:
        print("\n" + "="*70)
        print("ERROR: INITIALIZATION FAILED")
        print("="*70)
        print(f"\n{e}\n")
        print("="*70 + "\n")
        return 1
        
    except ValueError as e:
        LOG.error(f"Validation Error: {e}")
        print(f"\nValidation Error: {e}\n", file=sys.stderr)
        return 1
        
    except KeyboardInterrupt:
        LOG.info("Operation cancelled by user.")
        print("\n\nOperation cancelled by user.\n")
        return 1
        
    except Exception as e:
        LOG.exception("Unexpected error occurred")
        print(f"\nUnexpected error: {e}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

from score import OpenAIEngagementChecker

checker = OpenAIEngagementChecker()
result = checker.check_engagement("hello how are you")