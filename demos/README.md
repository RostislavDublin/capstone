# Demo Scripts

Интерактивные демонстрационные скрипты для ручного тестирования и проверки функциональности системы AI Code Review.

## Что здесь

Эта папка содержит скрипты для **ручной проверки и демонстрации**, которые:
- Показывают работу системы в действии
- Полезны для отладки и разработки
- Используют реальные API (Gemini, GitHub, Vertex AI)
- **НЕ являются автоматическими тестами** (для этого есть `tests/`)

## 🟢 Рабочие демо

### 1. `demo_quality_guardian_agent.py` ⭐ **ГЛАВНЫЙ**
**ADK Multi-Agent Implementation - Production-Ready Architecture**

Демонстрирует полную работу Quality Guardian Agent с использованием Google ADK:
- Natural language commands → ADK Agent → Tool execution
- RAG Corpus integration (Vertex AI) для persistent storage
- Bootstrap → Sync → Query workflow
- GitHub API integration (real repository commits)

**Запуск:**
```bash
cd /Users/Rostislav_Dublin/src/drs/ai/capstone
python demos/demo_quality_guardian_agent.py 1
```

**Режимы:**
- Mode 1: Интерактивное меню (все 4 теста подряд)
- Mode 2: Bootstrap only (analyze N commits)
- Mode 3: Sync only (check for new commits)
- Mode 4: Query only (ask questions about audits)

**Требования:**
- GitHub token: `GITHUB_TOKEN` в `.env.dev`
- Google Cloud project: `GOOGLE_CLOUD_PROJECT`
- Test repository: `RostislavDublin/capstone-test-fixture`

**Пример вывода:**
```
✅ Loaded environment from .env.dev

╔════════════════════════════════════════════════════════════════════╗
║  Quality Guardian Agent Demo - ADK Implementation (Google Agent)   ║
╚════════════════════════════════════════════════════════════════════╝

TEST 1: Bootstrap with 5 commits
✓ Bootstrap agent completed analysis of 5 commits

TEST 2: Sync (check for new commits)
✓ Found 2 new commits, analysis complete

TEST 3: Query RAG
Question: What security issues were found?
✓ Query results: Found 3 SQL injection patterns...

TEST 4: Agent Capabilities
✓ Agent can handle: bootstrap, sync, query operations
```

---

### 2. `demo_memory.py`
**Memory Bank - Pattern Learning and Recognition**

Демонстрирует как Memory Bank:
- Хранит review patterns из code reviews
- Отслеживает частоту и acceptance rate паттернов
- Хранит team coding standards
- Вспоминает похожие паттерны during reviews
- Предоставляет статистику по выученным паттернам

**Запуск:**
```bash
cd /Users/Rostislav_Dublin/src/drs/ai/capstone
python demos/demo_memory.py
```

**Требования:**
- Нет внешних зависимостей (использует in-memory storage)

**Что демонстрируется:**
```
================================================================================
                     SCENARIO 1: Learning from Code Reviews                     
================================================================================

Review 1: Found SQL injection in PR #123
   ✓ Pattern stored: f0e5584598cce1ac
   ✓ Developer fixed the issue (accepted)

Review 2: Found similar SQL injection in PR #156
   ✓ Same pattern detected: True
   ✓ Frequency increased to 2

SCENARIO 2: Team Standards
   ✓ Stored: Always use type hints in function signatures
   ✓ Stored: Max line length is 88 characters (Black)

SCENARIO 3: Pattern Statistics
   Most common patterns:
   1. SQL injection: 3 occurrences (100% accepted)
   2. Missing error handling: 2 occurrences (50% accepted)
```

---

## 🔴 Устаревшие/сломанные демо

### `demo_context_caching.py`
**Статус:** ❌ Не работает (синтаксическая ошибка + устаревший API)

**Проблемы:**
- Написан для старого API (не Vertex AI)
- Использует несуществующий `client.caches.create()`
- Proof-of-concept, не интегрирован с текущей архитектурой

**Рекомендация:** Удалить или переписать для Vertex AI Context Caching API
└── RAGCorpusManager → Vertex AI RAG storage
```

---

## Как добавить новое демо

1. Создай скрипт `demo_*.py` в этой папке
2. Добавь docstring с описанием и примером запуска
3. Добавь секцию в этот README
4. Используй `sys.path.insert(0, str(Path(__file__).parent.parent / "src"))` для импортов

**Шаблон:**
```python
"""Demo script for [feature name].

Demonstrates [what it does].
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from your_module import YourClass


def main():
    """Run the demo."""
    print("🚀 Starting demo...")
    # Your demo code
    

if __name__ == "__main__":
    main()
```

## Важно

- **Не коммитить API ключи** в скрипты
- Демо **НЕ запускаются** в CI/CD
- Для автоматического тестирования используй `tests/`
- Демо могут **требовать external services** (Gemini API, GitHub API)

## См. также

- `tests/` - автоматические тесты (pytest)
- `scripts/` - утилиты для разработки и деплоя
- `docs/testing-strategy.md` - стратегия тестирования
