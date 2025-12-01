# Video Demo Script - AI Code Review Orchestration System

**Total Duration:** 3 minutes  
**Recording Method:** Screen recording + voiceover (or just text captions)  
**Tools:** OBS Studio / QuickTime / Loom (free options)

---

## SIMPLE RECORDING PLAN

**Option 1 - Easiest (No talking):**
1. Record terminal with `adk web`
2. Add text captions after
3. 2x speed for boring parts
4. Upload to YouTube as unlisted

**Option 2 - Quick voiceover:**
1. Record terminal
2. Record audio separately reading script
3. Combine in iMovie/OpenShot (free)

---

## SCRIPT (Read slowly, ~30 seconds per section)

### [0:00-0:30] INTRO - Problem & Solution

**SCREEN:** Show README.md in editor, scroll to "Problem Statement"

**SCRIPT:**
```
Engineering teams need continuous quality monitoring.
Traditional tools only catch issues at PR time.
This system analyzes repository history, detects quality trends,
and uses RAG to explain WHY quality changed.
Built with Google ADK and Gemini 2.0.
```

**ALTERNATIVE (shorter):**
```
AI-powered quality monitoring for code repositories.
Analyzes commit history, detects trends, explains root causes.
Multi-agent system using Google ADK and RAG.
```

---

### [0:30-1:00] ARCHITECTURE - Show the system

**SCREEN:** Show README.md architecture diagram (ASCII art)

**SCRIPT:**
```
4-level agent hierarchy.
Quality Guardian dispatcher routes commands.
Bootstrap agent scans history. Sync agent tracks new commits.
Query Orchestrator combines Firestore trends 
with RAG semantic search for root causes.
Data stored in both Firestore and Vertex AI RAG Corpus.
```

**ALTERNATIVE (simpler):**
```
Multi-agent system with 5 specialized agents.
Dispatcher routes to domain agents.
Domain agents use Firestore for trends and RAG for analysis.
```

**ACTION:** Scroll through diagram slowly (10 seconds on diagram)

---

### [1:00-1:30] DEMO 1 - Bootstrap & Trends

**SCREEN:** Terminal with `adk web` running

**PREP:**
```bash
cd capstone
source .venv/bin/activate
adk web src/agents/
# Opens http://localhost:8000
# Select "quality_guardian" agent
```

**SCRIPT:**
```
Let's analyze a test repository.
I'll ask: "Bootstrap RostislavDublin/quality-guardian-test-fixture 
and analyze the last 10 commits"

Watch the agent:
- Connects to GitHub
- Extracts 10 commits
- Runs security and complexity scans
- Stores results in Firestore and RAG

Now ask: "Show quality trends"
Agent queries Firestore for aggregated statistics.
```

**ACTIONS IN ADK WEB:**
1. Type: `Bootstrap RostislavDublin/quality-guardian-test-fixture and analyze the last 10 commits`
2. Wait for response (~30 seconds) - can speed up 2x in editing
3. Type: `Show quality trends for the repository`
4. Show response with stats

**WHAT TO SHOW:**
- Agent routing (quality_guardian → bootstrap)
- Tool calls (GitHub API, security scans)
- Success message with summary

---

### [1:30-2:00] DEMO 2 - Root Cause Analysis (RAG in action)

**SCREEN:** Same ADK web interface, continue conversation

**SCRIPT:**
```
Now ask: "Why did quality degrade in recent commits?"

This uses RAG semantic search.
The agent searches all commit audits,
finds patterns across multiple commits,
and provides specific evidence with commit SHAs and files.

Notice: All citations are grounded in real data.
No hallucinations. Tool.from_retrieval ensures this.
```

**ACTION IN ADK WEB:**
1. Type: `Why did quality degrade in recent commits?`
2. Wait for response
3. Highlight citations (commit SHAs, file names)

**WHAT TO EMPHASIZE:**
- "RAG semantic search" in narration
- Point to commit SHA citations in output
- Mention "grounded - no hallucinations"

---

### [2:00-2:30] DEMO 3 - Composite Query (Multi-agent orchestration)

**SCREEN:** Same ADK web interface

**SCRIPT:**
```
Finally, a composite query combining both capabilities.
Ask: "Show trends AND explain root causes"

The orchestrator detects this needs both agents,
calls them in parallel,
and merges the responses into one comprehensive analysis.

This shows advanced multi-agent coordination.
```

**ACTION IN ADK WEB:**
1. Type: `Show trends AND explain root causes for quality changes`
2. Wait for response
3. Scroll to show both sections (trends + root cause)

**WHAT TO SHOW:**
- Two distinct sections in response
- "TREND ASSESSMENT" header
- "ROOT CAUSE ANALYSIS" header
- Merged coherent output

---

### [2:30-3:00] WRAP UP - Impact & Tech

**SCREEN:** Split screen or quick cuts:
- Left: Terminal showing test results `pytest tests/ -v` (last few lines showing "114 passed")
- Right: README.md showing "Technology Stack" section

**SCRIPT:**
```
Production ready system:
- 114 automated tests
- Comprehensive error handling
- Deploy to Vertex AI with one command

Built with Google ADK, Gemini 2.0 Flash and 2.5,
Firestore for structured data,
and Vertex AI RAG for semantic search.

Real engineering problem, production architecture.
Thank you.
```

**ALTERNATIVE (simpler ending):**
```
114 tests. Production ready. 
Google ADK, Gemini, Firestore, RAG.
Solves real quality monitoring problems.
GitHub: RostislavDublin/capstone
```

---

## RECORDING CHECKLIST

### BEFORE RECORDING:

- [ ] Terminal font size: 16-18pt (readable in video)
- [ ] Terminal colors: High contrast theme
- [ ] Close unnecessary windows/tabs
- [ ] Hide desktop icons (⌘+Shift+H on Mac)
- [ ] Disable notifications (Do Not Disturb)
- [ ] Test ADK web is running: `adk web src/agents/`
- [ ] Have commands ready in text file (copy-paste)
- [ ] Test repository already bootstrapped (faster demo)

### RECORDING SETTINGS:

- [ ] Resolution: 1920x1080 (Full HD)
- [ ] Frame rate: 30fps minimum
- [ ] Audio: 48kHz if recording voice
- [ ] Record internal audio if showing terminal output sounds

### AFTER RECORDING:

- [ ] Speed up slow parts (2x) - especially waiting for API calls
- [ ] Add text captions for key points
- [ ] Add title slide (0:00): "AI Code Review Orchestration System"
- [ ] Add end slide (3:00): "GitHub: RostislavDublin/capstone"
- [ ] Export: MP4, H.264, 1920x1080, 30fps

---

## EVEN SIMPLER VERSION (2 minutes)

If 3 minutes is too long:

### [0:00-0:30] Problem + Architecture
- Show README (10 sec)
- Show diagram (20 sec)
- Voiceover: "Multi-agent quality monitoring with RAG"

### [0:30-1:30] ONE Demo - Bootstrap
- `adk web` interface
- Bootstrap command
- Show results
- Voiceover: "Analyzes commits, stores in Firestore and RAG"

### [1:30-2:00] Wrap Up
- Show tests passing
- Show tech stack
- Done

---

## TIPS FOR FAST RECORDING

1. **Pre-bootstrap the repository** - Demo will run faster
   ```bash
   python demos/demo_quality_guardian_agent.py 1
   ```

2. **Use text-to-speech** - No need to record your voice
   - macOS: `say -v Samantha -f script.txt -o audio.aiff`
   - Online: Natural Reader, Google Text-to-Speech

3. **Use free tools:**
   - Recording: QuickTime (Mac) / OBS Studio (free, all platforms)
   - Editing: iMovie (Mac) / OpenShot (free, all platforms)
   - Captions: YouTube auto-generate (edit after upload)

4. **Don't aim for perfection:**
   - One take is fine if it shows the system working
   - Can speed up boring parts in editing
   - Text captions can fix unclear audio

5. **Fallback option - Silent video:**
   - Record screen only
   - Add detailed text captions
   - Background music (optional)
   - Still effective!

---

## UPLOAD INSTRUCTIONS

**YouTube (recommended):**
1. Upload as "Unlisted" (shareable via link only)
2. Title: "AI Code Review Orchestration System - Kaggle Capstone Demo"
3. Description: Copy from README.md overview
4. Add link to README.md in video description

**Alternative - Loom:**
1. Free screen recording with instant sharing
2. No editing needed
3. Get shareable link immediately

**Add to README:**
```markdown
## 🎥 Video Demo

Watch the 3-minute demo: [YouTube Link](https://youtu.be/YOUR_VIDEO_ID)
```

---

## FALLBACK: ANIMATED GIF DEMO

If video is too complex, create GIF:

```bash
# Use Kap (free Mac screen recorder) or Peek (Linux)
# Record 30-second demo
# Export as GIF
# Add to README:
```

```markdown
![Demo](demo.gif)
```

**Pros:** No audio needed, faster to make, embeds in README  
**Cons:** Limited duration, lower quality

---

## SAMPLE COMMANDS TO COPY-PASTE

```
Bootstrap RostislavDublin/quality-guardian-test-fixture and analyze the last 10 commits
```

```
Show quality trends for the repository
```

```
Why did quality degrade in recent commits?
```

```
Show trends AND explain root causes for quality changes
```

---

**Remember:** Simple is better than perfect. Show that it works.
