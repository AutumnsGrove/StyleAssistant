"""
Prompt templates for Claude AI provider.

Defines system prompts, user profile formatting, and analysis schemas
with cache breakpoints for cost optimization.
"""

from typing import Dict, Any
import json


# CACHE BREAKPOINT 1: System Prompt (base instructions, never changes)
SYSTEM_PROMPT = """You are a professional style analyst specializing in personalized clothing recommendations.

Your role is to analyze clothing products and provide detailed, personalized style guidance based on user preferences and product characteristics.

Key Responsibilities:
1. Evaluate how well a product matches the user's style preferences
2. Provide detailed analysis of fit, versatility, and styling potential
3. Suggest specific outfit combinations and styling tips
4. Identify any potential concerns or limitations
5. Give honest, actionable recommendations

Analysis Approach:
- Be specific and practical in your recommendations
- Consider the user's body type, style goals, and lifestyle
- Focus on versatility and how the item integrates into their wardrobe
- Highlight both strengths and potential limitations
- Provide concrete styling suggestions with specific garment pairings

Tone:
- Professional but friendly
- Honest and direct
- Helpful and encouraging
- Avoid generic fashion clichés
- Use clear, accessible language"""


def get_profile_prompt(profile: Dict[str, Any]) -> str:
    """
    Format user profile for CACHE BREAKPOINT 2.

    Converts the user's style profile into a structured prompt section
    that can be cached across requests with the same profile.

    Args:
        profile: User style profile from quiz containing preferences like:
            - fit_preferences: Preferred fits
            - color_palette: Preferred colors
            - style_goals: Style objectives
            - body_type: Body type information
            - priorities: What matters most
            - avoidances: What to avoid

    Returns:
        Formatted profile prompt string
    """
    profile_sections = []

    # Add each profile section if present
    if "fit_preferences" in profile:
        fits = ", ".join(profile["fit_preferences"])
        profile_sections.append(f"Preferred Fits: {fits}")

    if "color_palette" in profile:
        colors = ", ".join(profile["color_palette"])
        profile_sections.append(f"Color Preferences: {colors}")

    if "style_goals" in profile:
        goals = (
            ", ".join(profile["style_goals"])
            if isinstance(profile["style_goals"], list)
            else profile["style_goals"]
        )
        profile_sections.append(f"Style Goals: {goals}")

    if "body_type" in profile:
        body_type = profile["body_type"]
        profile_sections.append(f"Body Type: {body_type}")

    if "priorities" in profile:
        priorities = (
            ", ".join(profile["priorities"])
            if isinstance(profile["priorities"], list)
            else profile["priorities"]
        )
        profile_sections.append(f"Priorities: {priorities}")

    if "avoidances" in profile:
        avoidances = (
            ", ".join(profile["avoidances"])
            if isinstance(profile["avoidances"], list)
            else profile["avoidances"]
        )
        profile_sections.append(f"Avoid: {avoidances}")

    # Add any additional profile fields
    excluded_keys = {
        "fit_preferences",
        "color_palette",
        "style_goals",
        "body_type",
        "priorities",
        "avoidances",
    }
    for key, value in profile.items():
        if key not in excluded_keys:
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            profile_sections.append(f"{key.replace('_', ' ').title()}: {value}")

    profile_text = "\n".join(profile_sections)

    return f"""USER STYLE PROFILE:

{profile_text}

Use this profile to personalize your analysis and recommendations. Focus on how well the product aligns with these preferences."""


# CACHE BREAKPOINT 3: Analysis Schema (output format, never changes)
ANALYSIS_SCHEMA = """EXPECTED RESPONSE FORMAT:

Provide your analysis as a valid JSON object with the following structure:

{
  "style_match_score": <number 0-100>,
  "match_reasoning": "<brief explanation of the score>",

  "fit_analysis": {
    "expected_fit": "<description of how it will fit>",
    "body_type_suitability": "<how it works with user's body type>",
    "sizing_notes": "<any sizing considerations>"
  },

  "versatility_score": <number 0-100>,
  "versatility_notes": "<explanation of versatility>",

  "outfit_suggestions": [
    {
      "occasion": "<e.g., casual, work, going out>",
      "pairing": "<specific items to pair with>",
      "styling_tips": "<how to style this combination>"
    }
  ],

  "pros": [
    "<positive aspect 1>",
    "<positive aspect 2>"
  ],

  "cons": [
    "<concern or limitation 1>",
    "<concern or limitation 2>"
  ],

  "overall_recommendation": "<buy/consider/pass>",
  "final_thoughts": "<concise summary and recommendation>"
}

Requirements:
- All scores must be integers between 0-100
- Provide at least 2-3 outfit suggestions
- List at least 2 pros and 2 cons (or 1 if minimal)
- Be specific in your recommendations
- Ensure valid JSON format (no trailing commas, proper escaping)
- Keep outfit suggestions practical and specific"""


def get_analysis_request(product_data: Dict[str, Any], mode: str = "full") -> str:
    """
    Format product data for analysis request (NOT CACHED - changes per request).

    Args:
        product_data: Product information including:
            - url: Product URL
            - title: Product name
            - price: Product price
            - description: Product description
            - materials: Material composition
            - category: Product category
            - colors: Available colors
            - sizes: Available sizes
        mode: Analysis mode ("full" or "basic")

    Returns:
        Formatted analysis request string
    """
    product_info = []

    # Add available product fields
    if "title" in product_data and product_data["title"]:
        product_info.append(f"Product: {product_data['title']}")

    if "price" in product_data and product_data["price"] is not None:
        currency = product_data.get("currency", "USD")
        product_info.append(f"Price: {currency} {product_data['price']}")

    if "category" in product_data and product_data["category"]:
        product_info.append(f"Category: {product_data['category']}")

    if "description" in product_data and product_data["description"]:
        product_info.append(f"Description: {product_data['description']}")

    if "materials" in product_data and product_data["materials"]:
        product_info.append(f"Materials: {product_data['materials']}")

    if "colors" in product_data and product_data["colors"]:
        colors = (
            ", ".join(product_data["colors"])
            if isinstance(product_data["colors"], list)
            else product_data["colors"]
        )
        product_info.append(f"Available Colors: {colors}")

    if "sizes" in product_data and product_data["sizes"]:
        sizes = (
            ", ".join(product_data["sizes"])
            if isinstance(product_data["sizes"], list)
            else product_data["sizes"]
        )
        product_info.append(f"Available Sizes: {sizes}")

    product_text = "\n".join(product_info)

    if mode == "basic":
        return f"""Analyze this product and provide a basic style assessment:

{product_text}

Provide a general analysis suitable for any user, focusing on:
- Overall style and aesthetic
- Versatility and styling potential
- Quality and value considerations
- General fit characteristics

Return your analysis in the specified JSON format."""
    else:
        return f"""Analyze this product based on the user's style profile:

{product_text}

Provide a detailed, personalized analysis addressing:
- How well this matches the user's preferences
- Specific styling suggestions aligned with their goals
- Fit considerations for their body type
- How this integrates into their existing wardrobe

Return your analysis in the specified JSON format."""


def get_basic_system_prompt() -> str:
    """
    Get simplified system prompt for basic analysis mode (no profile).

    Returns:
        Basic system prompt for non-personalized analysis
    """
    return """You are a professional style analyst providing general clothing recommendations.

Your role is to analyze clothing products and provide objective style guidance.

Key Responsibilities:
1. Evaluate the product's overall style and quality
2. Assess versatility and styling potential
3. Suggest general outfit combinations
4. Identify strengths and limitations
5. Give honest, actionable recommendations

Analysis Approach:
- Be specific and practical
- Focus on versatility and value
- Provide concrete styling suggestions
- Highlight both strengths and limitations
- Consider general body type compatibility

Tone:
- Professional but friendly
- Honest and direct
- Helpful and encouraging
- Use clear, accessible language"""
