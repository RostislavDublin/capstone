# AI Code Review Bot - v2 GitHub-First Architecture

GitHub-First implementation for the AI Code Review Bot.

## Structure

- `src/gh_integration/` - GitHub integration layer
  - `client.py` - PyGithub wrapper for GitHub API operations
  - `context.py` - PR context loading and representation
  - `webhooks.py` - Webhook event handling
- `src/agents/` - Analysis agents
  - `analyzer.py` - Security + complexity analysis
  - `formatter.py` - Review comment formatting
- `src/tools/` - Analysis tools
  - `security_scanner.py` - Bandit wrapper
  - `complexity_analyzer.py` - Radon wrapper
- `tests/fixtures/` - Test fixtures
  - `test_repo_manager.py` - Automatic test repo setup/teardown

## Integration Tests

Tests use **real GitHub API** with automatic test repository management.

### Setup

1. Create `.env` file:
```bash
cp .env.example .env
```

2. Add your GitHub token:
```env
GITHUB_TOKEN=your_token_here
```

Get token from: https://github.com/settings/tokens (scopes: `repo`, `write:discussion`)

### Running Tests

```bash
# All integration tests (auto-creates test repo and PRs)
pytest tests/integration -v -m integration

# Specific test file
pytest tests/integration/test_analyzer.py -v -m integration

# With output
pytest tests/integration -v -m integration -s
```

### How Test Fixtures Work

1. **First run**: Creates `test-code-review-app` repository, initializes with test app
2. **Each test session**: Creates fresh PRs with unique branch names (timestamp)
3. **After tests**: Closes PRs and deletes branches (repo stays for reuse)
4. **Idempotent**: Can run tests multiple times without conflicts

## API Coverage

### GitHubClient
- ✅ Get repository
- ✅ Get pull request
- ✅ Get PR diff (unified format)
- ✅ Get PR files (with patches)
- ✅ Get review comments (inline on diff)
- ✅ Get issue comments (general PR conversation)
- ✅ Create review comment (inline with line number)
- ✅ Reply to review comment (creates thread)
- ✅ Create PR comment (general, not tied to line)

### PRContextLoader
- ✅ Load complete PR context (all data in one call)
- ✅ Parse file changes with patches
- ✅ Parse review comments (inline)
- ✅ Parse issue comments (general)
- ✅ Include PR metadata (labels, draft status, etc.)

### WebhookHandler
- ✅ Parse PR opened event
- ✅ Parse PR synchronize event (new commits)
- ✅ Parse review comment created event
- ✅ Parse issue comment created event
- ✅ Ignore non-PR issue comments
- ✅ Ignore unknown events

## Next Steps

1. **Core Agents** - Adapt from v1:
   - Copy security scanner, complexity analyzer
   - Create Analyzer agent that works with PRContext
   - Format findings as inline review comments

2. **Memory Bank** - Vertex AI RAG:
   - Create Corpus for team standards
   - Implement Learner agent to parse feedback
   - Store extracted standards as documents

3. **Orchestration** - Connect everything:
   - Webhook → Load PR context → Run agents → Post comments
   - Handle learning from developer responses
