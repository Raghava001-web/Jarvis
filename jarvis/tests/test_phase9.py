"""Phase 9 Verification — AppFinder + Compound Commands"""
import sys, os
os.chdir(r'c:\Users\chrag\OneDrive\Documents\AI_Voice_Assistant')
sys.path.insert(0, '.')
sys.path.insert(0, 'jarvis')

PASSED = 0
FAILED = 0

def check(name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {name} {detail}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name} {detail}")

print("=" * 60)
print("PHASE 9 VERIFICATION")
print("=" * 60)

# 1. AppFinder - YouTube (WEB_APPS)
print("\n--- 1. AppFinder WEB_APPS ---")
try:
    from jarvis.core.app_finder import AppFinder, AppType
    af = AppFinder()
    
    yt = af.find("youtube")
    check("YouTube found", yt is not None)
    check("YouTube is WEB type", yt and yt.app_type == AppType.WEB)
    check("YouTube URL correct", yt and "youtube.com" in yt.path)
    
    gmail = af.find("gmail")
    check("Gmail found", gmail is not None and gmail.app_type == AppType.WEB)
    
    netflix = af.find("netflix")
    check("Netflix found", netflix is not None and netflix.app_type == AppType.WEB)
    
    calc = af.find("calculator")
    check("Calculator found", calc is not None and calc.app_type == AppType.SYSTEM)
except Exception as e:
    check("AppFinder WEB_APPS", False, str(e))

# 2. AppFinder - Typo Correction
print("\n--- 2. Typo Correction ---")
try:
    chatpgt = af.find("chatpgt")
    check("chatpgt -> chatgpt", chatpgt is not None, str(chatpgt.name if chatpgt else "None"))
    
    spotofy = af.find("spotofy")
    check("spotofy -> spotify", spotofy is not None, str(spotofy.name if spotofy else "None"))
    
    perplexty = af.find("perplexty")
    check("perplexty -> perplexity", perplexty is not None, str(perplexty.name if perplexty else "None"))
except Exception as e:
    check("Typo correction", False, str(e))

# 3. AppFinder - WhatsApp Beta
print("\n--- 3. WhatsApp Beta ---")
try:
    wa_beta = af.find("whatsapp beta")
    check("WhatsApp Beta found", wa_beta is not None, str(wa_beta.name if wa_beta else "None"))
except Exception as e:
    check("WhatsApp Beta", False, str(e))

# 4. Compound Command Splitting
print("\n--- 4. Compound Commands ---")
try:
    # Import the actual server class method
    from jarvis.gui.websocket_server import JARVISWebSocketServer
    server = JARVISWebSocketServer.__new__(JARVISWebSocketServer)
    
    # Test compound splitting
    r1 = server._split_compound_command("set alarm for 5 min and remind me to drink water in 10 min")
    check("Split alarm+reminder", len(r1) == 2, str(r1))
    
    r2 = server._split_compound_command("open youtube and play some music")
    check("Split open+play", len(r2) == 2, str(r2))
    
    # Should NOT split
    r3 = server._split_compound_command("search for bread and butter")
    check("No split 'bread and butter'", len(r3) == 1, str(r3))
    
    r4 = server._split_compound_command("what is the time")
    check("No split single command", len(r4) == 1, str(r4))
    
    r5 = server._split_compound_command("set alarm for 5 min and also remind me to drink water")
    check("Split with 'also'", len(r5) >= 2, str(r5))
except Exception as e:
    check("Compound splitting", False, str(e))

# 5. PDF/OCR/Screenshot handlers exist
print("\n--- 5. Handler Modules ---")
try:
    from jarvis.core.screenshot_handler import ScreenshotHandler
    sh = ScreenshotHandler()
    check("ScreenshotHandler", sh is not None)
except Exception as e:
    check("ScreenshotHandler", False, str(e))

try:
    from jarvis.core.ocr_handler import OCRHandler
    oh = OCRHandler()
    check("OCRHandler", oh is not None)
except Exception as e:
    check("OCRHandler", False, str(e))

try:
    from jarvis.core.pdf_handler import PDFHandler
    ph = PDFHandler()
    check("PDFHandler", ph is not None)
except Exception as e:
    check("PDFHandler import", False, str(e))

print("\n" + "=" * 60)
print(f"RESULTS: {PASSED} passed, {FAILED} failed")
print("=" * 60)
