"""Test the new JARVIS cognitive architecture"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.personality import JARVISPersonality

print("=" * 50)
print("JARVIS COGNITIVE ARCHITECTURE TEST")
print("=" * 50)

jp = JARVISPersonality()

print("\n--- GREETING ---")
print(jp.get_greeting())

print("\n--- PROCESS RISKY ACTION ---")
result = jp.cognition.process("delete all files")
print(f"Allowed: {result['allowed']}")
print(f"Risk Level: {result['risk']['level']}")
print(f"Risk Prob: {result['risk']['probability']}")
print(f"Response: {result['response_template']}")

print("\n--- PROCESS NORMAL ACTION ---")
result2 = jp.cognition.process("what is the weather")
print(f"Strategy: {result2['response_type']}")
print(f"Risk: {result2['risk']['level']}")

print("\n--- CONTEXT AWARENESS ---")
ctx = result2['context']
print(f"Time: {ctx['environment']['time_of_day']}")
print(f"User State: {ctx['user_state']}")

print("\n--- LEARN FROM FRUSTRATED USER ---")
jp.cognition.world.update_user_state("frustrated", 0.8)
result3 = jp.cognition.process("just do it")
print(f"Style brevity: {result3['style']['brevity']}")
print(f"Style wit: {result3['style']['wit']}")

print("\n--- PREDICTION ---")
prediction = jp.cognition.predictor.predict_user_need()
if prediction:
    print(f"Predicted: {prediction.outcome}")
    print(f"Confidence: {prediction.probability:.0%}")
    print(f"Reasoning: {prediction.reasoning}")
else:
    print("No prediction")

print("\n--- AI PROMPT ---")
prompt = jp.get_personality_prompt("tired")
print(prompt[:500] + "...")

print("\n" + "=" * 50)
print("ALL TESTS PASSED")
print("=" * 50)
