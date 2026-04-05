"""
JARVIS Feature Audit v2 — Tests through real pipeline
"""
import sys, os, asyncio, json, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class FakeWS:
    def __init__(self): self.msgs = []
    async def send(self, m): self.msgs.append(m)

async def main():
    try:
        from jarvis.gui.websocket_server import JARVISWebSocketServer
        server = JARVISWebSocketServer()
        ws = FakeWS()
        server.clients = {ws}
        
        tests = [
            # APP OPENING
            ('open file manager', 'opening'),
            ('open files', 'opening'),
            ('open wifi settings', 'opening'),
            ('open bluetooth', 'opening'),
            ('open perplexity', 'opening'),
            ('open store', 'opening'),
            ('open settings', 'opening'),
            ('open photos', 'opening'),
            ('open calculator', 'opening'),
            ('open chrome', 'opening'),
            
            # SYSTEM CONTROLS
            ('increase volume', 'volume'),
            ('decrease volume', 'volume'),
            ('mute', 'mute'),
            ('set volume to 50', '50'),
            ('increase brightness', 'brightness'),
            ('set brightness to 70', 'brightness'),
            
            # QUERIES
            ('what time is it', 'time'),
            ('what is geopolitics', None),
            ('who created you', 'raghav'),
            ('tell me a joke', None),
            ('define algorithm', 'algorithm'),
            ('tell me the news', 'headline'),
            
            # ALARMS & REMINDERS
            ('set alarm in 10 minutes', 'alarm'),
            ('set reminder to drink water', 'remind'),
            
            # SCREEN
            ('take a screenshot', 'screenshot'),
            ('alt tab', 'switch'),
            
            # COMPOUND
            ('set alarm in 5 minutes and open youtube', None),
            ('mute and take a screenshot', None),
        ]
        
        passes = 0
        fails = 0
        for cmd, check_word in tests:
            try:
                r = await asyncio.wait_for(server.process_command(cmd, ws), timeout=15)
                preview = (r or 'None')[:70]
                ok = True
                if check_word and check_word.lower() not in (r or '').lower():
                    ok = False
                if "couldn't find" in (r or '').lower():
                    ok = False
                tag = '[PASS]' if ok else '[FAIL]'
                print(f'  {tag} {cmd}: {preview}')
                if ok:
                    passes += 1
                else:
                    fails += 1
            except asyncio.TimeoutError:
                print(f'  [TIMEOUT] {cmd}')
                fails += 1
            except Exception as e:
                print(f'  [CRASH] {cmd}: {e}')
                fails += 1
        
        # SPEECH CORRECTION TEST
        print()
        corr_tests = [
            ('jio politics', 'geopolitics'),
            ('open you', 'open youtube'),
            ('para plexity', 'perplexity'),
        ]
        for inp, exp in corr_tests:
            r = server.perception._correct_speech(inp)
            ok = exp in r
            tag = '[PASS]' if ok else '[FAIL]'
            print(f'  {tag} Correction: {inp} -> {r}')
            if ok:
                passes += 1
            else:
                fails += 1
        
        total = passes + fails
        pct = int(100 * passes / total) if total > 0 else 0
        print(f'\n  RESULTS: {passes}/{total} passed ({pct}%)')
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
