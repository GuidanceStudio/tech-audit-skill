# Threat model — LLM-assisted code

Codebases with 30-70% AI-assisted authorship show different failure modes from human-only codebases. The patterns below are signals — none is a 🔴 alone, but a cluster is.

## Symptom 1 — clone density

LLMs reproduce their own patterns. The same 20-line code block appears in 5 files, with minor variations.

**Detect**:

```sh
npx jscpd . --min-tokens 50 --reporters consoleFull
# or
pmd cpd --minimum-tokens 50 --files . --language $LANG
```

Thresholds:
- Duplication >2% of codebase → 🟡.
- Single duplicated block >200 tokens or repeated >3× → 🟡 each.

**Fix**: extract the common slice. The LLM didn't think to.

## Symptom 2 — single-impl interfaces

```php
interface UserRepositoryInterface { ... }
class UserRepository implements UserRepositoryInterface { ... }
// Used in exactly one place; no test seam; no second impl.
```

```python
class BaseAgentService(ABC):
    @abstractmethod
    def run(self, ...): ...

class AgentService(BaseAgentService):
    def run(self, ...): ...   # the only concrete impl, ever
```

LLMs love this pattern because tutorials say "code to an interface". Without a second concrete impl or a test seam, the interface is bloat.

**Detect**:

```sh
# PHP
grep -rnE 'interface [A-Z]\w*(Repository|Service|Manager|Factory)\b' --include="*.php"

# Python
grep -rnE 'class [A-Z]\w*\(ABC\)|@abstractmethod' --include="*.py"

# TypeScript
grep -rnE '^interface [A-Z]\w+' --include="*.ts"
```

For each: count concrete implementations (`grep -rn 'class .* implements <Interface>'`). Single concrete impl + no mock-based test seam → 🟡.

**Fix**: inline the interface. Tests can mock concrete classes via `Mockery` / `unittest.mock` / `vi.fn()`.

## Symptom 3 — dead helpers

LLMs over-generate utility functions ("here's a helper for X just in case"). Many are never called.

**Detect**: see D1 — dead-tree scan. LLM-assisted projects have ~3× higher dead-function ratios.

## Symptom 4 — duplicate data shapes

```python
# schemas.py
class AgentSchema(BaseModel):
    id: UUID
    name: str
    tenant_id: UUID

# models.py
class Agent(Base):
    id: Mapped[UUID]
    name: Mapped[str]
    tenant_id: Mapped[UUID]

# dto.py
@dataclass
class AgentDTO:
    id: UUID
    name: str
    tenant_id: UUID
```

Three representations of the same thing. Maintenance hell — a new field requires changing 3 files, and they will drift.

**Fix**: pick one (usually the Pydantic model) and derive the others or drop them.

## Symptom 5 — "just in case" abstraction

`Promise<Result<T, E>>` types when `Promise<T>` + thrown errors would do. Generic `BaseService` / `BaseController` with no second use. Optional fields that should be required (LLM hedges).

**Detect**: code review by reading. Tools won't catch this — it's structural over-engineering.

## Symptom 6 — test homogeneity

LLMs write tests that cluster on the same scenarios. Edge cases the LLM finds plausible are over-tested; edge cases that a human would think of (locale bugs, off-by-ones, race conditions in async code) are under-tested.

**Mitigation**: every feature must have at least one human-authored adversarial test. The PR template can prompt for this.

## Symptom 7 — spec-vs-code drift

The devplan / TODO list says ✅ for a feature, but the code only implements 60% of what the devplan describes. LLMs check off tasks aggressively.

**Detect**: D2 method — devplan honesty spot-check. For each ✅, open the commit + verify what it actually does.

## Symptom 8 — over-comment density

LLMs over-explain mechanical steps in comments:

```python
# Increment the counter
counter += 1
# Now check if we hit the limit
if counter > LIMIT:
    # Raise an exception
    raise LimitExceeded()
```

Each comment restates what the next line does. Useful comments explain *why* a non-obvious choice was made.

**Detect**:

```sh
# Rough proxy
loc=$(find . -name '*.py' -exec wc -l {} \; | awk '{s+=$1} END {print s}')
comments=$(grep -rE '^\s*#' --include='*.py' . | wc -l)
echo "comment ratio: $(echo "scale=2; $comments / $loc * 100" | bc)%"
```

>15% comments-to-code without API documentation strings → 🟡 (likely paraphrase-comments).

## Process mitigation

1. **Provenance comment policy** (optional): tag heavy-AI files so future audits know where to look first.
2. **PR template prompt**: "Did you write at least one adversarial test for this change?" — catches Symptom 6.
3. **Quarterly D1 deep pass**: catches Symptoms 1-4 before they accrete to a refactor-blocking mass.

## Cross-references

- `dimensions/D01-code-essentiality.md`.
- `dimensions/D03-tests-as-adversaries.md` — for the test-homogeneity counter.
- `tools/jscpd.md`.
