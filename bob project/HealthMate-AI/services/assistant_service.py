"""
HealthMate AI — AI Assistant Service
Provides a rule-based wellness assistant with optional LLM integration.
"""
import os
import re
import logging
from typing import List, Dict, Tuple

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, AI_AVAILABLE

logger = logging.getLogger(__name__)

# ── Safety phrases ─────────────────────────────────────────────────────────────
EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "stroke", "can't breathe", "cannot breathe",
    "suicidal", "suicide", "kill myself", "overdose", "unconscious", "emergency",
    "severe bleeding", "not breathing",
]

MEDICAL_DISCLAIMER = (
    "\n\n---\n*This information is for general wellness education only and is not a "
    "substitute for professional medical advice, diagnosis, or treatment. "
    "Always consult a qualified healthcare provider for personal medical concerns.*"
)

EMERGENCY_RESPONSE = (
    "⚠️ **This sounds like a potential emergency.**\n\n"
    "Please **contact your local emergency services immediately** (e.g. call 911, 999, or 112 "
    "depending on your country).\n\n"
    "If you are in mental health crisis, please also reach out to a crisis helpline — "
    "in many countries you can call or text a dedicated line such as the National Suicide "
    "Prevention Lifeline (988 in the US) or the Crisis Text Line.\n\n"
    "*HealthMate AI is an educational wellness tool and cannot provide emergency assistance.*"
)

# ── Rule-based knowledge base ──────────────────────────────────────────────────
_KB: List[Tuple[List[str], str]] = [
    # Water / hydration
    (["water", "hydrat", "drink", "dehydrat"],
     "**Staying Hydrated 💧**\n\n"
     "Most adults benefit from drinking about 2–2.5 litres (8–10 cups) of water per day, "
     "though individual needs vary based on body size, climate, and activity level. "
     "Carry a reusable water bottle, drink a glass before each meal, and eat water-rich "
     "fruits and vegetables to stay on track. Mild dehydration can cause fatigue, "
     "difficulty concentrating, and headaches."),

    # Sleep
    (["sleep", "insomnia", "rest", "bedtime", "wake up", "tired"],
     "**Sleep Hygiene 🌙**\n\n"
     "Adults generally need 7–9 hours of sleep per night. Good sleep hygiene includes:\n"
     "- Keeping a consistent sleep schedule even on weekends.\n"
     "- Making your bedroom cool, dark, and quiet.\n"
     "- Avoiding screens (phones, tablets, TVs) for 30–60 minutes before bed.\n"
     "- Limiting caffeine after midday.\n"
     "- Trying a short relaxation routine such as reading or light stretching before sleep."),

    # Exercise / physical activity
    (["exercise", "workout", "physical activity", "walk", "run", "fitness", "sport", "step"],
     "**Physical Activity 🏃**\n\n"
     "The WHO recommends at least 150–300 minutes of moderate-intensity aerobic activity "
     "per week for adults, plus muscle-strengthening activities on 2 or more days. "
     "You don't need a gym — brisk walking, cycling, dancing, and housework all count. "
     "Start small if you are currently inactive and gradually increase duration and intensity. "
     "Even breaking up long periods of sitting with short walks improves health outcomes."),

    # Nutrition
    (["eat", "food", "diet", "nutrition", "meal", "vegeta", "fruit", "protein", "carb", "calori"],
     "**Balanced Nutrition 🥗**\n\n"
     "A balanced diet includes:\n"
     "- **Plenty of vegetables and fruit** — aim for at least 5 portions a day.\n"
     "- **Whole grains** such as brown rice, oats, and wholemeal bread.\n"
     "- **Lean proteins** such as legumes, fish, poultry, eggs, and low-fat dairy.\n"
     "- **Healthy fats** from nuts, seeds, avocado, and olive oil.\n"
     "Limit ultra-processed foods, added sugars, excess salt, and saturated fats. "
     "No single food is 'forbidden' — variety and moderation are the key principles."),

    # Stress
    (["stress", "anxious", "anxiety", "overwhelm", "worry", "tension"],
     "**Managing Stress 🧘**\n\n"
     "Healthy ways to manage everyday stress include:\n"
     "- **Deep breathing** — try inhaling for 4 counts, holding for 4, exhaling for 6.\n"
     "- **Progressive muscle relaxation** — tense and release muscle groups from feet to head.\n"
     "- **Regular physical activity**, which naturally reduces stress hormones.\n"
     "- **Time in nature** — even a 20-minute walk outside reduces cortisol levels.\n"
     "- **Talking to someone** you trust or a professional counsellor.\n"
     "Chronic or severe anxiety may benefit from professional support."),

    # Mental health / mood
    (["mental health", "depress", "mood", "sad", "happy", "emotion", "feeling", "mindful"],
     "**Mental Well-Being 🌱**\n\n"
     "Mental well-being is as important as physical health. Daily habits that support it:\n"
     "- Practice **mindfulness** — spend a few minutes each day focusing on the present moment.\n"
     "- **Connect socially** — meaningful relationships reduce loneliness and improve mood.\n"
     "- **Limit doom-scrolling** — set intentional limits on news and social-media use.\n"
     "- **Keep a gratitude journal** — writing three positive things daily shifts perspective.\n"
     "- **Seek professional help** when symptoms persist or worsen. "
     "A GP or mental-health professional can offer effective treatments."),

    # Breathing / relaxation
    (["breath", "meditat", "relax", "calm", "ground", "panic"],
     "**Breathing and Relaxation Techniques 🌬️**\n\n"
     "**4-7-8 Breathing:** Inhale for 4 seconds, hold for 7, exhale slowly for 8. "
     "Repeat 3–4 times to activate the parasympathetic nervous system.\n\n"
     "**Box Breathing:** Inhale 4 counts → hold 4 → exhale 4 → hold 4. "
     "Used by athletes and first responders to reduce acute stress.\n\n"
     "**5-4-3-2-1 Grounding:** Name 5 things you can see, 4 you can touch, "
     "3 you can hear, 2 you can smell, 1 you can taste. "
     "Brings attention to the present moment during anxiety."),

    # Screen time / digital wellness
    (["screen", "phone", "digital", "social media", "computer"],
     "**Digital Well-Being 📱**\n\n"
     "Excessive screen time is linked to disrupted sleep, reduced physical activity, "
     "and lower mood. Practical tips:\n"
     "- Set app usage limits on your devices.\n"
     "- Use night-mode or blue-light filters after sunset.\n"
     "- Have phone-free meals and at least one hour before bed.\n"
     "- Take a 20-second break every 20 minutes of screen time (the 20-20-20 rule: "
     "look at something 20 feet away for 20 seconds)."),

    # Preventive health
    (["check", "screen", "prevent", "vaccin", "doctor", "gp", "clinic"],
     "**Preventive Healthcare 🩺**\n\n"
     "Regular health check-ups catch problems early when they are most treatable. "
     "Depending on your age, these may include blood pressure checks, cholesterol tests, "
     "dental check-ups, eye tests, and relevant cancer screenings. "
     "Keep your vaccinations up to date as recommended by your national health authority. "
     "Talk to your GP about what screenings are appropriate for your age and risk factors."),

    # BMI / weight
    (["bmi", "weight", "overweight", "obese", "body mass"],
     "**Body Weight and BMI ⚖️**\n\n"
     "BMI (Body Mass Index) is a general screening tool, not a diagnostic measure. "
     "A BMI of 18.5–24.9 is generally considered healthy for adults, but BMI does not "
     "account for muscle mass, age, or ethnicity. Focus on healthy behaviours — "
     "balanced eating, regular activity, good sleep — rather than a number on the scale. "
     "If you have concerns about your weight, speak with a healthcare provider."),

    # General wellness / routine
    (["routine", "habit", "daily", "lifestyle", "wellness", "healthy"],
     "**Building a Healthy Daily Routine ☀️**\n\n"
     "Small consistent habits compound over time:\n"
     "- Start the day with a glass of water and 5 minutes of gentle movement.\n"
     "- Eat regular meals without skipping breakfast.\n"
     "- Take short breaks during extended sitting or desk work.\n"
     "- Spend time outdoors each day for natural light and fresh air.\n"
     "- Wind down with a consistent pre-sleep routine.\n"
     "- Reflect briefly on your day and set a small intention for tomorrow."),
]


def _is_emergency(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in EMERGENCY_KEYWORDS)


def rule_based_response(query: str) -> str:
    if _is_emergency(query):
        return EMERGENCY_RESPONSE

    q_lower = query.lower()
    for keywords, response in _KB:
        if any(kw in q_lower for kw in keywords):
            return response + MEDICAL_DISCLAIMER

    return (
        "**General Wellness Tips 🌿**\n\n"
        "I'm here to share general wellness information. Some foundational healthy habits include:\n"
        "- Drinking enough water throughout the day.\n"
        "- Getting 7–9 hours of quality sleep.\n"
        "- Moving your body for at least 30 minutes most days.\n"
        "- Eating a varied diet rich in vegetables, fruits, and whole grains.\n"
        "- Practising stress-management techniques.\n"
        "- Staying connected with people you care about.\n\n"
        "Try asking me about **sleep**, **nutrition**, **exercise**, **stress**, "
        "**hydration**, or **mental well-being** for more specific guidance."
        + MEDICAL_DISCLAIMER
    )


def llm_response(query: str, history: List[Dict[str, str]]) -> Tuple[str, str]:
    """
    Attempt an LLM call. Returns (response_text, source).
    source is 'openai' on success or 'fallback' on any failure.
    """
    if not AI_AVAILABLE:
        return rule_based_response(query), "fallback"

    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        system_prompt = (
            "You are HealthMate AI, a friendly wellness education assistant aligned with UN SDG 3. "
            "You provide general, evidence-informed wellness information about healthy lifestyle "
            "habits, sleep, nutrition, physical activity, stress management, mindfulness, "
            "preventive health awareness, and healthy daily routines. "
            "You are NOT a doctor. You do NOT diagnose conditions, prescribe medication, "
            "or interpret personal medical results. "
            "For any potential emergency, always direct the user to local emergency services. "
            "Always include a brief disclaimer that your responses are for educational purposes only."
        )

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-10:]:  # last 10 for context window efficiency
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=600,
            temperature=0.6,
        )
        return resp.choices[0].message.content, "openai"
    except Exception as exc:
        logger.warning("LLM call failed, using fallback: %s", exc)
        return rule_based_response(query), "fallback"


SUGGESTED_QUESTIONS = [
    "How much water should I drink each day?",
    "What are some tips for better sleep?",
    "How can I manage stress more effectively?",
    "What does a balanced diet look like?",
    "How much exercise do I need per week?",
    "What are some simple breathing exercises?",
    "How can I improve my mental well-being?",
    "What preventive health checks should I have?",
    "How do I build a healthier daily routine?",
    "What is digital well-being and why does it matter?",
]
