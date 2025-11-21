# Demo Scripts

Интерактивные демонстрационные скрипты для ручного тестирования и проверки функциональности системы AI Code Review.

## Что здесь

Эта папка содержит скрипты для **ручной проверки и демонстрации**, которые:
- Показывают работу системы в действии
- Полезны для отладки и разработки
- Используют реальные API (Gemini, GitHub)
- **НЕ являются автоматическими тестами** (для этого есть `tests/`)

## Доступные демо

### `demo_analyzer.py`
**Демонстрация Analyzer Agent с реальным PR diff**

Показывает как агент анализирует изменения кода:
1. Создает merged state (base repo + PR diff)
2. Запускает security scanner (bandit)
3. Анализирует complexity (radon)
4. Генерирует AI рекомендации через Gemini 2.0

**Запуск:**
```bash
cd /Users/Rostislav_Dublin/src/drs/ai/capstone
python demos/demo_analyzer.py
```

**Требования:**
- Google AI Studio API key в `.env` или переменной окружения
- Test fixture репозиторий: `tests/fixtures/test-app/`

**Пример вывода:**
```
Initializing Analyzer Agent...
Step 1: Parsing git diff...
Step 2: Creating merged repository (base + PR)...
   Merged state created at: /tmp/pr_review_xyz/repo
Step 3: Running security analysis...
   app/database.py: 3 issues (H:3 M:0 L:0)
Step 4: Analyzing code complexity...
Step 5: Generating AI recommendations...
```

---

### `demo_backend_integration.py`
**Backend Integration Test - GitHubConnector + AuditEngine**

**⚠️ Scope: Backend tools integration test only**
- Tests GitHubConnector API integration
- Tests AuditEngine (security + complexity analysis)
- Tests FileAudit models (per-file tracking)
- **NOT TESTED:** ADK Agent, RAG Corpus, orchestration layer

**Запуск:**
```bash
cd /Users/Rostislav_Dublin/src/drs/ai/capstone
python demos/demo_backend_integration.py
```

**Требования:**
- GitHub token в `.env.dev`: `GITHUB_TOKEN`
- Google Cloud credentials (for temp checkouts only, RAG not used yet)

**Что демонстрируется:**
```
╔══════════════════════════════════════════════════════════════════╗
║         🔍 QUALITY GUARDIAN AGENT DEMONSTRATION 🔍               ║
╚══════════════════════════════════════════════════════════════════╝

DEMO 1: Component Integration
   ✓ GitHub Connector - connects to RostislavDublin/capstone
   ✓ Bootstrap Handler - samples commits (recent/tags/date-range)
   ✓ Audit Engine - analyzes code quality and security
   ✓ RAG Storage Manager - stores audits in Vertex AI

DEMO 2: Bootstrap Workflow (Historical Scan)
   Command: 'bootstrap RostislavDublin/capstone strategy=recent count=3'
   ✅ Analyzed 3 commits
   📊 Commit Details:
      1. 880a499 - feat: Add Memory Bank implementation
         Files: 5, Lines: +234/-12
         File breakdown:
           • src/memory/schema.py (+145/-0)
           • tests/unit/test_memory_bank.py (+89/-0)

DEMO 3: Sync Workflow (Incremental Updates)
   Command: 'sync RostislavDublin/capstone'
   ✅ Repository is up to date!
   Last audited commit: 880a499
```

**Архитектура:**
```
QualityGuardianAgent (orchestrator)
├── RepositoryConnector → GitHub API
├── BootstrapHandler → Sampling strategies
├── AuditEngine → Security + Quality analysis
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
