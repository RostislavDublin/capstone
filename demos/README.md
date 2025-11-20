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
