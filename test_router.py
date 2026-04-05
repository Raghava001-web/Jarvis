"""Test the IntentRouter integration as it would be used in websocket_server.py"""
import os
import sys

# Test if the router setup in websocket_server works correctly
print("Testing IntentRouter integration...")

# Import as done in websocket_server
ROUTER_AVAILABLE = False
try:
    from jarvis.core.intent_router import IntentRouter, Intent, HandlerResult
    from jarvis.core.intent_classifier import classify_intent
    from jarvis.core.intent_handlers import HANDLER_MAP
    ROUTER_AVAILABLE = True
    print("[OK] IntentRouter and handlers available")
except ImportError as e:
    print(f"[FAIL] IntentRouter not available: {e}")

if not ROUTER_AVAILABLE:
    print("Cannot continue test - router not available")
    sys.exit(1)

# Simulate the _init_jarvis setup
router = None
if ROUTER_AVAILABLE:
    try:
        router = IntentRouter()
        for intent_name, handler in HANDLER_MAP.items():
            router.register_by_name(intent_name, handler)
        print(f"[OK] IntentRouter initialized with {len(HANDLER_MAP)} handlers")
        print(f"[OK] Handlers: {list(HANDLER_MAP.keys())}")
    except Exception as e:
        print(f"[FAIL] IntentRouter init error: {e}")

# Simulate _route_through_router
def _route_through_router(command: str):
    """Route command through IntentRouter - returns None if no handler found"""
    if not router or not ROUTER_AVAILABLE:
        print(f"  [DEBUG] Router not available: router={router}, ROUTER_AVAILABLE={ROUTER_AVAILABLE}")
        return None
    
    try:
        # Classify the intent
        intent_name, entities = classify_intent(command)
        print(f"  [DEBUG] Classified: intent_name={intent_name}, entities={entities}")
        
        # Build context with all available services
        context = {
            'title': 'sir',
            'assistant_name': 'JARVIS',
            'is_friday': False,
            'knowledge': None,  # Would be initialized in real server
            'weather_handler': None,
            'system_stats': {'cpu': 30, 'memory': 50, 'disk': 60, 'battery': 100, 'charging': False},
            'news_handler': None,
            'system_control': None,
        }
        
        # Route to handler
        result = router.route_by_name(intent_name, command, entities, context)
        print(f"  [DEBUG] Result: success={result.success}, response={result.response[:60]}...")
        
        if result and result.success:
            return result.response
        elif result and not result.success and "I don't know" not in result.response:
            return result.response
        
        return None
        
    except Exception as e:
        print(f"  [FAIL] Router error: {e}")
        import traceback
        traceback.print_exc()
        return None

# Test commands
print("\n" + "="*60)
print("Testing commands through _route_through_router:")
print("="*60)

test_commands = [
    "hello",
    "what time is it",
    "tell me a joke",
    "who created you",
    "what's the weather",
    "switch to friday",  # This should NOT be handled by router
]

for cmd in test_commands:
    print(f"\nCommand: \"{cmd}\"")
    response = _route_through_router(cmd)
    if response:
        print(f"  -> Response: {response}")
    else:
        print(f"  -> No response (would fall back to legacy)")
