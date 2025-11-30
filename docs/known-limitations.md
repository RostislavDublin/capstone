# Known Limitations - Quality Guardian v1.0

## Attribution Granularity

### File-Level Attribution (Current Implementation)

**Design Decision:** Quality changes are attributed at the file level, not diff level.

**Team Practice:** "If you touch a file, you improve it!"

When a developer modifies a file:
- They are responsible for the FINAL quality score of that file after their commit
- Trend analysis compares file quality before/after their changes
- If file quality improves → credited to developer
- If file quality declines → developer is responsible

### Why File-Level Attribution?

**Pragmatic for MVP:**
- Simpler implementation (no diff-level issue tracking needed)
- Matches real team workflows (file-level code ownership)
- Motivates developers to improve entire file when making changes
- Avoids complex "which line caused which issue" analysis

**Example Scenarios:**

1. **Developer adds feature to problematic file:**
   - File had quality score 60/100 (old security issues)
   - Developer adds new function
   - They also fix existing security issues while there
   - Final score: 90/100
   - **Attribution:** Developer gets credit for improvement

2. **Developer makes small change to clean file:**
   - File had quality score 95/100
   - Developer adds hardcoded password in their change
   - Final score: 70/100
   - **Attribution:** Developer responsible for decline

3. **Intentional refactoring:**
   - Developer sees file with score 50/100
   - Makes no functional changes, just fixes quality issues
   - Final score: 95/100
   - **Attribution:** Developer gets credit (encouraged behavior!)

### What This Means for Analysis

**query_trends tool:**
- Compares file quality scores before/after each commit
- Attributes improvement/decline to commit author
- Focuses on NET EFFECT on codebase quality
- Encourages "boy scout rule" (leave code better than you found it)

**What we DON'T track (v1.0):**
- Issue-by-issue attribution (which author introduced which specific issue)
- Diff-level granularity (quality of changed lines only)
- Inherited vs new issues distinction
- Multi-author file collaboration patterns

### Future Enhancement (Post-MVP)

If needed for more sophisticated teams:
- Diff-level analysis (compare issues in changed lines only)
- Issue lifecycle tracking (who introduced, who fixed)
- Collaborative file ownership patterns
- Technical debt inheritance tracking

### Why This Limitation Is Acceptable

**For 90% of use cases, PMs want to know:**
1. "What's broken NOW?" → Latest commit analysis (works)
2. "Who's improving quality?" → File-level attribution (works)
3. "Any regressions?" → Commit-to-commit comparison (works)

**Rare edge cases we don't handle:**
- "Developer inherited 100 issues but only changed 1 line" → Still responsible for final state
- Solution: Team discipline + code reviews catch this

### Team Culture Implication

This design reinforces healthy development practices:
- Don't ignore existing issues in files you touch
- Take ownership of file quality
- Refactoring is encouraged and credited
- Quality is everyone's responsibility

**TL;DR:** Attribution is at file level. Touch a file → you own its final quality. Simple, pragmatic, MVP-ready.
