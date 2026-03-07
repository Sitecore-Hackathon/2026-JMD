import os
import json
import logging
from typing import List, Optional, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

# ==========================================
# LOGGING
# ==========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("content-analyzer-api")

app = FastAPI(title="Sitecore Content Analyzer API")


# ==========================================
# MODELS
# ==========================================
class FieldInput(BaseModel):
    name: str
    currentValue: str
    previousValue: Optional[str] = ""


class AnalyzeRequest(BaseModel):
    itemId: str
    itemName: str
    fields: List[FieldInput]


# ==========================================
# HEALTH
# ==========================================
@app.get("/health")
def health():
    return {"status": "ok"}


# ==========================================
# HELPERS
# ==========================================
def clean_json_text(text: str) -> str:
    if not text:
        return "{}"

    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def safe_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []


def safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def strict_scoring_rules() -> str:
    return """
STRICT SCORING RULES:
Use the full score range and do NOT be generous.

0-20:
- Empty, meaningless, random, broken, or extremely poor content
- No SEO value, no clarity, no structure

21-40:
- Very weak content
- Extremely short, vague, repetitive, poor relevance
- Little to no engagement or search value

41-60:
- Basic but below average content
- Some meaning exists, but weak structure, weak wording, weak SEO
- Limited usefulness to users

61-75:
- Acceptable content
- Understandable and somewhat useful
- Missing stronger keywords, structure, clarity, or persuasive quality

76-89:
- Strong content
- Clear, relevant, useful, and reasonably optimized
- Minor issues only

90-100:
- Excellent content
- Highly clear, compelling, well-structured, highly relevant, and strongly optimized

IMPORTANT:
- Random text, placeholder text, or vague text must score low.
- Very short titles like "About 1" should not get high SEO or engagement scores.
- Empty fields must score very low.
"""


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def call_openai_json(prompt: str) -> dict:
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    client = get_client()

    try:
        response = client.responses.create(
            model=model_name,
            input=prompt
        )

        output_text = clean_json_text(response.output_text)
        logger.info("Model output: %s", output_text)

        return json.loads(output_text)

    except json.JSONDecodeError as ex:
        logger.exception("JSON parsing failed. Model did not return valid JSON.")
        return {
            "_error": f"Invalid JSON from model: {str(ex)}"
        }

    except Exception as ex:
        logger.exception("OpenAI call failed.")
        return {
            "_error": f"OpenAI call failed: {str(ex)}"
        }


def fallback_field_result(field_name: str) -> dict:
    return {
        "fieldName": field_name,
        "engagementScore": 0,
        "seoScore": 0,
        "sentiment": "Neutral",
        "seoSuggestions": ["Unable to generate SEO suggestions."],
        "contentSuggestions": ["Unable to generate content suggestions."]
    }


def fallback_overall_result() -> dict:
    return {
        "engagementScore": 0,
        "seoScore": 0,
        "sentiment": {
            "label": "Neutral",
            "confidence": 0
        },
        "versionComparison": {
            "summary": "Analysis could not be fully completed.",
            "improvedFields": [],
            "declinedFields": []
        }
    }


# ==========================================
# ANALYZE
# ==========================================
@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        meaningful_fields = []

        for field in request.fields:
            current_value = field.currentValue or ""
            previous_value = field.previousValue or ""

            if current_value.strip() == "" and previous_value.strip() == "":
                continue

            meaningful_fields.append(field)

        if not meaningful_fields:
            return {
                "itemId": request.itemId,
                "itemName": request.itemName,
                "analysis": {
                    "engagementScore": 0,
                    "seoScore": 0,
                    "sentiment": {"label": "Neutral", "confidence": 0},
                    "versionComparison": {
                        "summary": "No analyzable field content found.",
                        "improvedFields": [],
                        "declinedFields": []
                    },
                    "fieldResults": []
                }
            }

        # ==========================================
        # FIELD-LEVEL ANALYSIS
        # ==========================================
        field_results = []

        for field in meaningful_fields:
            current_value = field.currentValue or ""
            previous_value = field.previousValue or ""

            field_prompt = f"""
You are an AI content analyzer for Sitecore.

Analyze this single field independently and return ONLY valid JSON.

{strict_scoring_rules()}

FIELD NAME:
{field.name}

CURRENT VALUE:
{current_value}

PREVIOUS VALUE:
{previous_value}

SCORING EXPECTATIONS:
- engagementScore: clarity, usefulness, reader interest, persuasiveness, readability
- seoScore: keyword relevance, title/search usefulness, structure, discoverability
- sentiment: Positive, Neutral, or Negative
- seoSuggestions: only SEO-specific suggestions
- contentSuggestions: only readability, clarity, engagement, and tone suggestions

Return JSON in exactly this format:
{{
  "fieldName": "{field.name}",
  "engagementScore": 0,
  "seoScore": 0,
  "sentiment": "Positive/Neutral/Negative",
  "seoSuggestions": [],
  "contentSuggestions": []
}}

RULES:
- Scores must be integers from 0 to 100.
- Evaluate ONLY this field, not the whole page.
- Do not repeat the same suggestion in both arrays.
- Return at most 3 seoSuggestions and 3 contentSuggestions.
- If the content is weak, vague, random, too short, or empty, score it low.
- Return ONLY JSON. No markdown. No explanation.
"""

            raw_field_result = call_openai_json(field_prompt)

            if "_error" in raw_field_result:
                logger.warning("Field analysis fallback used for field: %s", field.name)
                field_results.append(fallback_field_result(field.name))
                continue

            field_results.append({
                "fieldName": safe_str(raw_field_result.get("fieldName"), field.name),
                "engagementScore": safe_int(raw_field_result.get("engagementScore"), 0),
                "seoScore": safe_int(raw_field_result.get("seoScore"), 0),
                "sentiment": safe_str(raw_field_result.get("sentiment"), "Neutral"),
                "seoSuggestions": safe_list(raw_field_result.get("seoSuggestions")),
                "contentSuggestions": safe_list(raw_field_result.get("contentSuggestions"))
            })

        # ==========================================
        # OVERALL ANALYSIS
        # ==========================================
        current_text_parts = []
        previous_text_parts = []

        for field in meaningful_fields:
            current_text_parts.append(f"{field.name}: {field.currentValue or ''}")
            previous_text_parts.append(f"{field.name}: {field.previousValue or ''}")

        current_text = "\n".join(current_text_parts)
        previous_text = "\n".join(previous_text_parts)

        overall_prompt = f"""
You are an AI content quality analyzer for Sitecore content authors.

Analyze the entire item content and compare CURRENT content with PREVIOUS version.

{strict_scoring_rules()}

CURRENT CONTENT:
{current_text}

PREVIOUS CONTENT:
{previous_text}

SCORING EXPECTATIONS:
- engagementScore: user interest, usefulness, clarity, persuasiveness, readability
- seoScore: search visibility potential, keyword usefulness, title relevance, structural quality
- sentiment.label: Positive, Neutral, or Negative
- sentiment.confidence: integer 0 to 100
- versionComparison.summary: concise explanation of whether current content improved or declined
- improvedFields / declinedFields: actual field names

Return ONLY valid JSON in exactly this format:
{{
  "engagementScore": 0,
  "seoScore": 0,
  "sentiment": {{
    "label": "Positive/Neutral/Negative",
    "confidence": 0
  }},
  "versionComparison": {{
    "summary": "",
    "improvedFields": [],
    "declinedFields": []
  }}
}}

RULES:
- Scores must be integers from 0 to 100.
- confidence must be an integer from 0 to 100.
- Random, vague, or filler-heavy content must not receive high scores.
- Very short or generic text should score low to moderate, not high.
- Return ONLY JSON. No markdown. No explanation.
"""

        raw_overall_result = call_openai_json(overall_prompt)

        if "_error" in raw_overall_result:
            logger.warning("Overall analysis fallback used.")
            overall_result = fallback_overall_result()
        else:
            sentiment_obj = raw_overall_result.get("sentiment", {})
            version_obj = raw_overall_result.get("versionComparison", {})

            overall_result = {
                "engagementScore": safe_int(raw_overall_result.get("engagementScore"), 0),
                "seoScore": safe_int(raw_overall_result.get("seoScore"), 0),
                "sentiment": {
                    "label": safe_str(sentiment_obj.get("label"), "Neutral"),
                    "confidence": safe_int(sentiment_obj.get("confidence"), 0)
                },
                "versionComparison": {
                    "summary": safe_str(version_obj.get("summary"), ""),
                    "improvedFields": safe_list(version_obj.get("improvedFields")),
                    "declinedFields": safe_list(version_obj.get("declinedFields"))
                }
            }

        return {
            "itemId": request.itemId,
            "itemName": request.itemName,
            "analysis": {
                "engagementScore": overall_result["engagementScore"],
                "seoScore": overall_result["seoScore"],
                "sentiment": overall_result["sentiment"],
                "versionComparison": overall_result["versionComparison"],
                "fieldResults": field_results
            }
        }

    except HTTPException:
        raise
    except Exception as ex:
        logger.exception("Unhandled error in /analyze")
        raise HTTPException(status_code=500, detail=str(ex))