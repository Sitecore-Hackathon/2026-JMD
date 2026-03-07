import sys
import json
import re

from difflib import SequenceMatcher
from bs4 import BeautifulSoup

# Attempt to import OpenAIEngagementChecker from openai.py module
try:
    from openai import OpenAIEngagementChecker
except ImportError:
    OpenAIEngagementChecker = None

 # Attempt to import the check_individual_engagement function from score.py
# try:
#     from openai import check_individual_engagement
# except ImportError:
#     check_individual_engagement = None



def clean_rte(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ")

def _tokenize(text: str):
    # simple word tokenizer (keeps alphanumerics)
    return re.findall(r"\b\w+\b", text.lower())


def _syllable_count(word: str) -> int:
    """Rudimentary syllable counter for English words."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    # common short words
    if len(w) <= 3:
        return 1
    # count vowel groups as syllables
    groups = re.findall(r"[aeiouy]+", w)
    count = len(groups)
    # subtract silent 'e'
    if w.endswith("e"):
        # but not if word ends with 'le' preceded by consonant (e.g., 'table')
        if not (w.endswith("le") and len(w) > 2 and w[-3] not in "aeiouy"):
            count = max(1, count - 1)
    return max(1, count)


def flesch_reading_ease(text: str) -> float:
    """Compute Flesch Reading Ease score (approximate).

    Returns a float; higher means easier to read.
    """
    if not text or not text.strip():
        return 0.0
    sentences = re.split(r"[.!?]+", text)
    sentences = [s for s in sentences if s.strip()]
    num_sentences = max(1, len(sentences))
    words = re.findall(r"\b[\w']+\b", text)
    num_words = max(1, len(words))
    syllables = sum(_syllable_count(w) for w in words)
    # Flesch Reading Ease formula
    score = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (syllables / num_words)
    return round(score, 2)


def textstat(s1: str, s2: str):
    """
    Return simple statistics for two strings.
    Returns a dict so caller can inspect individual metrics.
    """
    t1 = _tokenize(s1)
    t2 = _tokenize(s2)

    set1 = set(t1)
    set2 = set(t2)

    common = set1.intersection(set2)
    union = set1.union(set2)
    score1 = flesch_reading_ease(s1)
    score2 = flesch_reading_ease(s2)

    stats = {
        "word_count_1": len(t1),
        "word_count_2": len(t2),
        "char_count_1": len(s1),
        "char_count_2": len(s2),
        "unique_words_1": len(set1),
        "unique_words_2": len(set2),
        "common_words_count": len(common),
        "jaccard_similarity": (len(common) / len(union)) if union else 1.0,
        "common_words": sorted(common),
        "score_1_readability": score1,
        "score_2_readability": score2,
    }
    return stats


_POSITIVE_WORDS = {
        "good",
        "great",
        "happy",
        "excellent",
        "nice",
        "love",
        "awesome",
        "fantastic",
        "positive",
        "fortunate",
        "pleased",
        "enjoy",
}
_NEGATIVE_WORDS = {
    "bad",
    "sad",
    "terrible",
    "awful",
    "hate",
    "horrible",
    "poor",
    "negative",
    "unfortunate",
    "angry",
    "disappointed",
}


def _simple_sentiment_score(tokens):
    if not tokens:
        return 0.0
    pos = sum(1 for t in tokens if t in _POSITIVE_WORDS)
    neg = sum(1 for t in tokens if t in _NEGATIVE_WORDS)
    # normalize to range [-1, 1]
    score = (pos - neg) / len(tokens)
    return round(score, 4)


def sentiment(s1: str, s2: str):
    """
    Return sentiment scores for each string and an overall summary.
    Scores are simple heuristics (-1.0 .. 1.0).
    """
    t1 = _tokenize(s1)
    t2 = _tokenize(s2)

    score1 = _simple_sentiment_score(t1)
    score2 = _simple_sentiment_score(t2)
    avg = round((score1 + score2) / 2, 4)

    return {
        "sentiment_score_1": score1,
        "sentiment_score_2": score2,
        "average_sentiment": avg,
    }


def _print_json_and_exit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    input("Press Enter to continue...")


def _usage():
    return (
        "Usage: python PythonApplication1.py <case> <string1> <string2>\n\n"
        "Cases:\n"
        "  textstat   - return text statistics for the two strings\n"
        "  sentiment  - return simple sentiment scores for each string\n"
        "  score      - evaluate individual visitor engagement scores for each string using OpenAI\n"
        "  compare    - compare engagement scores between two strings and show which is more engaging\n"
       #"  openai     - evaluate individual visitor engagement using OpenAI checker\n"
        "Note: If strings contain spaces, wrap them in quotes."
    )


if __name__ == "__main__":
    # If insufficient command-line arguments are provided, prompt the user interactively.
    if len(sys.argv) < 4:
        try:
            case = input("Enter case (textstat | sentiment | openai score | compare): ").strip().lower()
            s1 = input("Enter first string: ").strip()
            s2 = input("Enter second string: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("Input cancelled.")
            sys.exit(1)
    else:
        case = sys.argv[1].lower()
        s1 =  clean_rte(sys.argv[2])
        s2 = clean_rte(sys.argv[3])

    if case == "textstat":
        result = textstat(s1, s2)
        _print_json_and_exit(result)
        
    elif case == "sentiment":
        result = sentiment(s1, s2)
        _print_json_and_exit(result)
        
    elif case == "score":
        # Use OpenAIEngagementChecker to evaluate individual engagement scores
        if OpenAIEngagementChecker is None:
            error_result = {
                "error": "OpenAIEngagementChecker not available. Ensure score.py is installed and OPENAI_API_KEY is set."
            }
            _print_json_and_exit(error_result)
            sys.exit(2)
        
        try:
            print("Initializing OpenAI Engagement Checker...")
            checker = OpenAIEngagementChecker()
            
            print("Evaluating individual engagement scores for both strings...\n")
            
            # Evaluate each string individually
            print(f"Evaluating first string: {s1[:50]}...")
            first_result = checker.check_engagement(s1)
            
            print(f"Evaluating second string: {s2[:50]}...")
            second_result = checker.check_engagement(s2)
            
            # Compile results
            result = {
                "evaluation_type": "individual_engagement_scores",
                "first_string": {
                    "content_preview": s1[:100] + "..." if len(s1) > 100 else s1,
                    "content_length": len(s1),
                    "word_count": len(s1.split()),
                    "engagement_result": first_result
                },
                "second_string": {
                    "content_preview": s2[:100] + "..." if len(s2) > 100 else s2,
                    "content_length": len(s2),
                    "word_count": len(s2.split()),
                    "engagement_result": second_result
                }
            }
            
            _print_json_and_exit(result)
            
        except Exception as exc:
            error_result = {
                "error": "Individual engagement evaluation failed",
                "detail": str(exc),
                "suggestion": "Ensure OPENAI_API_KEY environment variable is set correctly"
            }
            _print_json_and_exit(error_result)
            sys.exit(4)

    elif case == "compare":
        # Compare engagement scores between two strings and show which is more engaging
        if OpenAIEngagementChecker is None:
            error_result = {
                "error": "OpenAIEngagementChecker not available. Ensure score.py is installed and OPENAI_API_KEY is set."
            }
            _print_json_and_exit(error_result)
            sys.exit(2)
        
        try:
            print("\n" + "="*70)
            print("COMPARING ENGAGEMENT SCORES")
            print("="*70 + "\n")
            print("Initializing OpenAI Engagement Checker...")
            checker = OpenAIEngagementChecker()
            
            print("Evaluating engagement for both strings...\n")
            
            # Evaluate each string individually
            print(f"[1/2] Evaluating first string: {s1[:60]}...")
            first_result = checker.check_engagement(s1)
            first_score = first_result.get("overall_engagement_score", 0)
            first_label = first_result.get("engagement_label", "Unknown")
            
            print(f"[2/2] Evaluating second string: {s2[:60]}...")
            second_result = checker.check_engagement(s2)
            second_score = second_result.get("overall_engagement_score", 0)
            second_label = second_result.get("engagement_label", "Unknown")
            
            # Calculate comparison metrics
            score_difference = abs(first_score - second_score)
            winner = "first" if first_score > second_score else ("second" if second_score > first_score else "tie")
            
            # Compile comprehensive comparison results
            result = {
                "evaluation_type": "engagement_comparison",
                "comparison_summary": {
                    "winner": winner,
                    "score_difference": score_difference,
                    "summary": (
                        f"String 1 is MORE ENGAGING (score difference: {score_difference} points)"
                        if winner == "first"
                        else (
                            f"String 2 is MORE ENGAGING (score difference: {score_difference} points)"
                            if winner == "second"
                            else "Both strings have EQUAL ENGAGEMENT scores"
                        )
                    )
                },
                "first_string": {
                    "content_preview": s1[:80] + "..." if len(s1) > 80 else s1,
                    "content_length": len(s1),
                    "word_count": len(s1.split()),
                    "overall_engagement_score": first_score,
                    "engagement_label": first_label,
                    "detailed_scores": first_result.get("detailed_scores", {}),
                    "strengths": first_result.get("strengths", []),
                    "improvement_suggestions": first_result.get("improvement_suggestions", [])
                },
                "second_string": {
                    "content_preview": s2[:80] + "..." if len(s2) > 80 else s2,
                    "content_length": len(s2),
                    "word_count": len(s2.split()),
                    "overall_engagement_score": second_score,
                    "engagement_label": second_label,
                    "detailed_scores": second_result.get("detailed_scores", {}),
                    "strengths": second_result.get("strengths", []),
                    "improvement_suggestions": second_result.get("improvement_suggestions", [])
                },
                "detailed_comparison": {
                    "clarity_difference": abs(
                        first_result.get("detailed_scores", {}).get("clarity", 0) -
                        second_result.get("detailed_scores", {}).get("clarity", 0)
                    ),
                    "emotional_appeal_difference": abs(
                        first_result.get("detailed_scores", {}).get("emotional_appeal", 0) -
                        second_result.get("detailed_scores", {}).get("emotional_appeal", 0)
                    ),
                    "persuasiveness_difference": abs(
                        first_result.get("detailed_scores", {}).get("persuasiveness", 0) -
                        second_result.get("detailed_scores", {}).get("persuasiveness", 0)
                    ),
                    "cta_strength_difference": abs(
                        first_result.get("detailed_scores", {}).get("call_to_action_strength", 0) -
                        second_result.get("detailed_scores", {}).get("call_to_action_strength", 0)
                    ),
                    "structure_quality_difference": abs(
                        first_result.get("detailed_scores", {}).get("structure_quality", 0) -
                        second_result.get("detailed_scores", {}).get("structure_quality", 0)
                    )
                }
            }
            
            _print_json_and_exit(result)
            
        except Exception as exc:
            error_result = {
                "error": "Engagement comparison failed",
                "detail": str(exc),
                "suggestion": "Ensure OPENAI_API_KEY environment variable is set correctly"
            }
            _print_json_and_exit(error_result)
            sys.exit(4)

    # elif case == "openai":
    #     # Alternative OpenAI evaluation case (kept for backward compatibility)
    #     if OpenAIEngagementChecker is None:
    #         error_result = {
    #             "error": "OpenAIEngagementChecker not available. Ensure score.py is installed and OPENAI_API_KEY is set."
    #         }
    #         _print_json_and_exit(error_result)
    #         sys.exit(2)

    #     try:
    #         print("Initializing OpenAI Engagement Checker...\n")
    #         checker = OpenAIEngagementChecker()
            
    #         # Get individual evaluations
    #         print(f"Evaluating engagement for first string: {s1[:50]}...")
    #         first_result = checker.check_engagement(s1)
            
    #         print(f"Evaluating engagement for second string: {s2[:50]}...")
    #         second_result = checker.check_engagement(s2)
            
    #         # Also evaluate combined text
    #         combined_text = f"{s1}\n\n{s2}"
    #         print("Evaluating combined text engagement...")
    #         combined_result = checker.check_engagement(combined_text)
            
    #         result = {
    #             "evaluation_type": "comprehensive_engagement",
    #             "first": first_result,
    #             "second": second_result,
    #             "combined": combined_result,
    #         }
    #         _print_json_and_exit(result)
            
    #     except Exception as exc:
    #         error_result = {
    #             "error": "OpenAI evaluation failed",
    #             "detail": str(exc),
    #             "suggestion": "Ensure OPENAI_API_KEY environment variable is set correctly"
    #         }
    #         _print_json_and_exit(error_result)
    #         sys.exit(4)
            
    else:
        print(f"Unknown case: {case}\n")
        print(_usage())
        sys.exit(3)