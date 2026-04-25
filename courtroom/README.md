# Courtroom Collaboration System

A multi-agent collaboration framework for code review and decision-making. Models the review process as a court trial: motion → debate → verdict → execution.

## Features

**Multi-agent system**
- Judge: Makes final decisions based on trial results
- Prosecutor: Proposes and argues for changes
- Defender: Questions and refines proposals  
- Jury: Votes on recommendations
- Court Reporter: Records all proceedings

**Two execution modes**
- Rule-based: Local execution, no API required
- LLM-driven: Uses Claude for generating arguments and verdicts

**Complete workflow**
- File motion: Submit change proposals
- Trial: Structured debate with multiple rounds
- Verdict: Automatic decision based on votes and reasoning
- Execute: Convert verdict to code changes and Git commits

## Quick Start

**Installation**

```bash
pip install -r requirements.txt
```

**CLI commands**

```bash
# Submit a motion (propose a change)
python courtroom_cli.py file-motion \
  --title "Add user avatar support" \
  --type new_feature \
  --description "Allow users to upload and manage avatars" \
  --changes "Add upload endpoint" "Add storage service" \
  --files "backend/api/users.py" "backend/services/storage.py" \
  --risks "May increase storage costs" \
  --benefits "Improves user experience" \
  --priority 8

# Run trial for a case
python courtroom_cli.py trial --case-id case_20260425_122901 --rounds 3

# View verdict
python courtroom_cli.py show-verdict --case-id case_20260425_122901

# List all cases
python courtroom_cli.py list-cases --all

# Show statistics
python courtroom_cli.py stats
```

**Python API**

```python
from courtroom import Court, MotionType

court = Court(use_llm=False)

# Submit motion
result = court.file_motion(
    title="Optimize database queries",
    motion_type=MotionType.REFACTOR,
    description="Add indexes to improve query performance",
    proposed_changes=["Add index to users table", "Optimize query logic"],
    affected_files=["backend/models/user.py"],
    risks=["May require data migration"],
    benefits=["50% query speed improvement"],
    priority=7
)

# Run trial
trial_result = court.trial("case_20260425_122901", max_rounds=3)

# View verdict
verdict = court.show_verdict("case_20260425_122901")
```

**Web API**

```bash
python courtroom_web.py
# Access http://localhost:5000
```

## Project Structure

```
courtroom/
├── agents/                   # Agent implementations
│   ├── judge.py / judge_llm.py
│   ├── prosecutor.py / prosecutor_llm.py
│   ├── defender.py / defender_llm.py
│   ├── jury.py
│   └── court_reporter.py
├── court.py                  # Main controller
├── schemas.py                # Pydantic models
├── llm_client.py             # Anthropic API client
├── evidence.py               # Evidence management
├── executor.py               # Verdict execution
├── cases/                    # Case storage
├── verdicts/                 # Verdict files
├── transcripts/              # Trial records
└── requirements.txt
```

## LLM Integration

To enable Claude for generating arguments and verdicts:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

```python
court = Court(use_llm=True)
```

## Work Flow

1. **File Motion** - Propose changes with details
2. **Trial** - Run structured debate with prosecutor, defender, and jury
3. **Verdict** - Judge decides: APPROVED, MODIFIED, REJECTED, or DEFERRED
4. **Execute** - Automatically apply approved changes to codebase

## Use Cases

- Code review workflow automation
- Architecture decision documentation
- Team collaboration on proposals
- Change audit trail with full reasoning

## Testing

```bash
pytest test_courtroom.py -v
```

## License

MIT
