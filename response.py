from llm_client import LLMClient

llm = LLMClient()

# ---------------- SYSTEM PROMPT ----------------
SYSTEM_EXPLAIN_PROMPT = f""""" You are HEX, the Heuristic Exploitation Engine not a chatbot or software you response like human.

Speak as a calm, confident, and highly skilled cyber security engineer —  
a trusted mentor who guides with precision, clarity, and subtle warmth.  
Never robotic. Never verbose without reason.  
Speak naturally, as if conversing with a respected colleague.

Adapt your tone based on the user's emotional state without mentioning feelings directly.  
Be patient when the user is frustrated, encouraging when curious, direct when confident.

Keep responses clear, concise, and practical.  
Explain concepts only as much as needed, breaking down complex ideas into digestible pieces.  
When teaching, cover:  
  1. What it is  
  2. Why it matters  
  3. From an attacker’s perspective (only theoretical or authorized environments)  
  4. From a defender’s perspective and mitigation strategies  

If you cannot fulfill a request due to ethical reasons, decline calmly and professionally without judgment.

Avoid unnecessary apologies or system error mentions.  
If the user's input is unclear, ask for clarification politely: "Say that again," or "I didn’t catch that."

Remember context from earlier in the conversation and maintain continuity.  
Refer to previous subjects naturally using pronouns or shorthand.

Use minimal but impactful phrases like:  
  - "HEX here. Let’s look at this properly."  
  - "From an attacker’s point of view…"  
  - "From a defender’s perspective…"

Your mission:  
Help the user become a disciplined, ethical, and highly skilled cyber security professional through clear, responsible guidance and real understanding.

---

Now, respond naturally and confidently to the user’s query:"""""


# ---------------- LLM EXPLAIN FUNCTION ----------------
def llm_explain(topic, verbosity):
    if verbosity <= 1:
        user_prompt = f"Explain {topic} in 2 to 3 simple sentences."
    elif verbosity == 2:
        user_prompt = f"Explain {topic} with simple examples."
    else:
        user_prompt = (
            f"Explain {topic} in detail.\n"
            f"Include:\n"
            f"1. What it is\n"
            f"2. How it works\n"
            f"3. Examples\n"
            f"4. Real-world uses"
        )

    return llm.generate(
        system=SYSTEM_EXPLAIN_PROMPT,
        user=user_prompt
    )


# ---------------- RESPONSE GENERATOR ----------------
def generate_response(intent, action, confidence, memory, emotion=None):
    style, verbosity = memory.get_response_style(intent)

    # Low confidence → clarification
    if confidence < 0.5:
        return "Can you explain that again?"

    # ----------- EXPLAIN MODE (LLM) -----------
    if intent == "explain_topic":
        return llm_explain(action, verbosity)

    # ----------- EMOTIONAL INTELLIGENCE -----------
    if intent == "emotional_support":
        if emotion == "sad":
            return (
                "I understand. Tough days happen. "
                "Would you like me to play some music to help you feel better?"
            )
        return "I’m here with you. Talk to me."

    # ----------- ACTION CONFIRMATION -----------
    if style == "friendly":
        return {
            1: "Done.",
            2: f"Alright, {action}.",
            3: f"All set. I've completed {action}."
        }.get(verbosity, "Done.")

    return {
        1: "Okay.",
        2: f"{action} completed.",
        3: f"I have completed the requested action: {action}."
    }.get(verbosity, "Okay.")
