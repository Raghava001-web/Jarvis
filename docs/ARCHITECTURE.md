# JARVIS Architecture

## High-Level System Diagram

```mermaid
flowchart TD
    subgraph Input["🎤 Input Layer"]
        USER[User Voice/Text]
        PERCEPTION[Perception Module]
    end

    subgraph Understanding["🧠 Understanding Layer"]
        CONTEXT[Context Memory]
        EMOTION[Emotion Router]
        INTENT[Intent Model<br/>kNN + Centroid]
        ENTITY[Entity Extractor<br/>spaCy + Regex]
    end

    subgraph State["📊 State Layer"]
        STATE[State Manager<br/>Single Source of Truth]
        DECISION[Decision Engine<br/>Reasoning Layer]
    end

    subgraph Action["⚡ Action Layer"]
        ROUTER[Intent Router]
        PERSONALITY[JARVIS Personality<br/>Iron Man Style]
        HANDLERS[Handlers]
    end

    subgraph Memory["💾 Memory Layer"]
        WORKING[Working Memory<br/>Auto-Summarization]
        LONGTERM[Long-Term Memory<br/>Semantic Embeddings]
        PROACTIVE[Proactive Assistant<br/>Pattern Learning]
    end

    subgraph Output["🔊 Output Layer"]
        TTS[Text-to-Speech]
        RESPONSE[Response]
    end

    USER --> PERCEPTION
    PERCEPTION --> CONTEXT
    CONTEXT --> |Pronoun Resolution| EMOTION
    EMOTION --> |Mood Update| INTENT
    INTENT --> |Classification| ENTITY
    ENTITY --> STATE
    STATE --> DECISION
    DECISION --> |PROCEED/WARN/CLARIFY| ROUTER
    ROUTER --> HANDLERS
    HANDLERS --> PERSONALITY
    PERSONALITY --> TTS
    TTS --> RESPONSE

    STATE --> WORKING
    STATE --> LONGTERM
    ROUTER --> PROACTIVE
```

## Pipeline Flow

```mermaid
sequenceDiagram
    participant U as User
    participant P as Perception
    participant CM as Context Memory
    participant ER as Emotion Router
    participant IM as Intent Model
    participant EE as Entity Extractor
    participant SM as State Manager
    participant DE as Decision Engine
    participant IR as Intent Router
    participant H as Handler
    participant PY as Personality
    participant M as Memory

    U->>P: "play blinding lights on spotify"
    P->>CM: resolve_pronoun(text)
    CM-->>ER: resolved text
    ER->>SM: set user_mood
    ER->>IM: classify(text)
    IM-->>IM: kNN + centroid scoring
    IM-->>ER: (play_music, 0.95)
    ER->>EE: extract(text, intent)
    EE-->>SM: {song, app}
    SM->>DE: decide(intent, entities)
    DE-->>IR: PROCEED
    IR->>H: handle_play(entities)
    H-->>PY: "Playing Blinding Lights"
    PY-->>U: styled response + challenge
    IR->>M: add_exchange()
```

## Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| **Perception** | Voice recognition, TTS output |
| **Context Memory** | Pronoun resolution, working memory, summarization |
| **Emotion Router** | Detect user mood, update state |
| **Intent Model** | Classify intent (kNN + centroid + rejection) |
| **Entity Extractor** | Extract entities (spaCy + regex hybrid) |
| **State Manager** | Single source of truth for all state |
| **Decision Engine** | Reason about HOW to handle (warn/clarify/refuse) |
| **Intent Router** | Dispatch to correct handler |
| **Personality** | Iron Man style, challenges, wit |
| **Handlers** | Music, Alarm, Apps, Search, etc. |
| **Proactive Assistant** | Pattern learning, suggestions |

## Decision Engine Flow

```mermaid
flowchart LR
    subgraph Decisions
        A[Intent + Entities] --> B{Check Safety}
        B --> |Shutdown| C[CLARIFY]
        B --> |Safe| D{Check Context}
        D --> |Late Night| E[WARN_THEN_PROCEED]
        D --> |Normal| F{Check Confidence}
        F --> |< 0.50| G[CLARIFY]
        F --> |< 0.65| H[SUGGEST_ALTERNATIVE]
        F --> |>= 0.65| I[PROCEED]
    end
```

## File Structure

```
jarvis/
├── jarvis_ultimate.py       # Main brain
├── core/
│   ├── intent_model.py      # kNN + centroid classifier
│   ├── intent_definitions.py # Training examples
│   ├── entity_extractor.py  # spaCy + regex
│   ├── state_manager.py     # Single source of truth
│   ├── decision_engine.py   # Reasoning layer
│   ├── intent_router.py     # Dispatch logic
│   ├── personality.py       # Iron Man style
│   ├── context_memory.py    # Working + long-term
│   ├── emotion_router.py    # Mood detection
│   ├── proactive_assistant.py # Pattern learning
│   └── logger.py            # Structured logging
└── tests/
    ├── test_intent_model.py
    ├── test_intent_router.py
    └── test_entity_extractor.py
```
