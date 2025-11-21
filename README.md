# GitHub Integration Layer

GitHub-First implementation for the AI Code Review Bot.

## Structure

- `src/github/` - GitHub integration layer
  - `client.py` - PyGithub wrapper for GitHub API operations
  - `context.py` - PR context loading and representation
  - `webhooks.py` - Webhook event handling

## Integration Tests

Tests use real GitHub API calls. To run:

1. Create `.env` file:
```bash
cp .env.example .env
```

2. Add your GitHub token and test repo:
```
GITHUB_TOKEN=your_github_token_here
TEST_REPO=RostislavDublin/test-code-review
TEST_PR_NUMBER=1
```

3. Run tests:
```bash
# All integration tests
pytest tests/integration -v -m integration

# Specific test file
pytest tests/integration/test_github_client.py -v -m integration
```

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
