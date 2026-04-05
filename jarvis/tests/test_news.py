"""
JARVIS Feature Test #5: News Handler
Tests: Fetching news by category
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("  JARVIS Feature Test #5: News Handler")
print("=" * 60)
print()

# Try to import
try:
    from core.news_handler import NewsHandler
    print("[OK] NewsHandler imported successfully")
except ImportError as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)

# Mock perception for news handler
class MockPerception:
    def speak(self, text):
        print(f"JARVIS: {text}")

perception = MockPerception()

# Initialize
print("\n[1] Initializing NewsHandler...")
try:
    news = NewsHandler(perception)
    print("[OK] NewsHandler initialized")
except Exception as e:
    print(f"[FAIL] Init error: {e}")
    sys.exit(1)

# List categories
print("\n[2] Available News Categories:")
for cat in news.categories.keys():
    print(f"    - {cat}")

# Test fetching news
print("\n[3] Testing News Fetching by Category...")
test_categories = ["general", "technology", "business", "sports", "politics"]

for category in test_categories:
    print(f"\n    --- {category.upper()} ---")
    try:
        # Use get_category_news
        news.get_category_news(category, count=3)
    except Exception as e:
        print(f"    [ERROR] {e}")

# Summary
print("\n" + "=" * 60)
print("  Test Complete - News Handler")
print("=" * 60)
print("""
Results:
- Check if news headlines were fetched for each category
- News is cached for 1 hour to avoid repeated API calls

If news fetching worked, it's ready for HUD integration!
""")
