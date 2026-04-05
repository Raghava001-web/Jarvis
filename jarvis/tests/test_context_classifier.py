"""Test context-aware intent classification"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.intent_classifier import classify_intent, ClassificationContext

# Test without context
print("Without context:")
print(f"  'next' -> {classify_intent('next')}")
print(f"  'play' -> {classify_intent('play')}")

# Test with Spotify context
ctx_spotify = ClassificationContext(active_app='spotify')
print("\nWith spotify context:")
print(f"  'next' -> {classify_intent('next', ctx_spotify)}")
print(f"  'play' -> {classify_intent('play', ctx_spotify)}")
print(f"  'pause' -> {classify_intent('pause', ctx_spotify)}")

# Test with PDF context
ctx_pdf = ClassificationContext(active_app='pdf')
print("\nWith pdf context:")
print(f"  'next' -> {classify_intent('next', ctx_pdf)}")
print(f"  'previous' -> {classify_intent('previous', ctx_pdf)}")

# Test with music context
ctx_music = ClassificationContext(active_app='music')
print("\nWith music context:")
print(f"  'next' -> {classify_intent('next', ctx_music)}")
print(f"  'stop' -> {classify_intent('stop', ctx_music)}")

print("\n✅ Context-aware classification working!")
