"""
JARVIS Structured Logger
========================
Pipeline-aware logging: INPUT → INTENT → ROUTE → STATE → RESPONSE
Replaces scattered print() statements with consistent, filterable output.
"""

import logging
import sys
from datetime import datetime
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# FORMATTER: Structured pipeline output
# ═══════════════════════════════════════════════════════════════════════════════

class JarvisFormatter(logging.Formatter):
    """Custom formatter: [STAGE] message with color support"""
    
    COLORS = {
        'INPUT':    '\033[96m',   # Cyan
        'INTENT':   '\033[93m',   # Yellow
        'ROUTE':    '\033[95m',   # Magenta
        'STATE':    '\033[94m',   # Blue
        'RESPONSE': '\033[92m',   # Green
        'ERROR':    '\033[91m',   # Red
        'WARN':     '\033[33m',   # Orange
        'SYSTEM':   '\033[90m',   # Gray
        'RESET':    '\033[0m',
    }
    
    def format(self, record):
        stage = getattr(record, 'stage', 'SYSTEM')
        color = self.COLORS.get(stage, self.COLORS['SYSTEM'])
        reset = self.COLORS['RESET']
        
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        msg = record.getMessage()
        
        # Include source file info for errors
        if stage == 'ERROR':
            return f"{color}[{timestamp}] [{stage}] {msg} ({record.filename}:{record.lineno}){reset}"
        
        return f"{color}[{timestamp}] [{stage}] {msg}{reset}"


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGER: Pipeline-aware methods
# ═══════════════════════════════════════════════════════════════════════════════

class JarvisLogger:
    """Structured logger for the JARVIS pipeline."""
    
    def __init__(self, name: str = "jarvis"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JarvisFormatter())
            self.logger.addHandler(handler)
        
        self.logger.propagate = False
    
    def _log(self, stage: str, message: str, level=logging.INFO):
        self.logger.log(level, message, extra={'stage': stage})
    
    # ── Pipeline stages ──────────────────────────────────────────────────
    
    def input(self, source: str, text: str):
        """Log incoming user input. source: 'voice', 'text', 'gesture', 'button'"""
        self._log('INPUT', f'source={source} text="{text}"')
    
    def intent(self, intent_name: str, confidence: float = 0.0, 
               entities: Optional[dict] = None, context: Optional[str] = None):
        """Log classified intent."""
        parts = [f'{intent_name} ({confidence:.2f})']
        if entities:
            # Only log non-empty entities
            filtered = {k: v for k, v in entities.items() if v}
            if filtered:
                parts.append(f'entities={filtered}')
        if context:
            parts.append(f'context={context}')
        self._log('INTENT', ' '.join(parts))
    
    def route(self, handler: str, method: str = ''):
        """Log which handler is processing the command."""
        if method:
            self._log('ROUTE', f'{handler}.{method}()')
        else:
            self._log('ROUTE', handler)
    
    def state(self, **kwargs):
        """Log state changes. Pass key=value pairs."""
        parts = [f'{k}={v}' for k, v in kwargs.items() if v is not None]
        if parts:
            self._log('STATE', ' '.join(parts))
    
    def response(self, text: str, spoken: bool = False):
        """Log outgoing response."""
        prefix = '[SPEAK]' if spoken else '[TEXT]'
        # Truncate long responses
        display = text[:100] + '...' if len(text) > 100 else text
        self._log('RESPONSE', f'{prefix} "{display}"')
    
    def error(self, message: str, exc: Optional[Exception] = None):
        """Log errors with optional exception."""
        if exc:
            self._log('ERROR', f'{message}: {type(exc).__name__}: {exc}', logging.ERROR)
        else:
            self._log('ERROR', message, logging.ERROR)
    
    def warn(self, message: str):
        """Log warnings."""
        self._log('WARN', message, logging.WARNING)
    
    def system(self, message: str):
        """Log system-level messages (init, shutdown, etc)."""
        self._log('SYSTEM', message)


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON: Global logger instance
# ═══════════════════════════════════════════════════════════════════════════════

_logger = None

def get_logger() -> JarvisLogger:
    """Get the global JARVIS logger instance."""
    global _logger
    if _logger is None:
        _logger = JarvisLogger()
    return _logger

# Convenience alias
log = get_logger
