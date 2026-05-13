"""
CEN 350 - Theory of Computation
PDA Simulator: Nested Block Delimiter Language
Project Code: 12
Domain   : Programming Block Syntax (Domain 2)
Constraint: Two nested structure types only — { } and ( )
Feature  : Accept only canonical/normalized forms

CANONICAL FORM RULES:
  1. Only two delimiter types are allowed: { } and ( )
  2. A string is canonical if it is properly nested AND
     outer-level blocks always use { } before ( )
     — i.e. at the top level, all { } groups come before all ( ) groups.
  3. Empty string ε is canonical.
  4. At any single nesting level, { } pairs must appear before ( ) pairs.

Example canonical:    {}()   {()}   {{}}   ({})  ← outer { wraps ()
Example NON-canonical: (){}  ← at top level, () appears before {} → not normalized
"""

OPEN   = {'{': '{', '(': '('}
CLOSE  = {'}': '{', ')': '('}
BOTTOM = '$'


# ─────────────────────────────────────────────
#  Phase 1 — PDA: check proper nesting (two types only)
# ─────────────────────────────────────────────

def simulate_nesting(tokens: list) -> dict:
    """Check that the string is properly nested using only { } and ( )."""
    state  = 'q0'
    stack  = [BOTTOM]
    trace  = []

    trace.append({
        'step': 0, 'state': state,
        'remaining': ''.join(tokens),
        'stack': list(stack),
        'action': 'Start — check proper nesting'
    })

    for i, sym in enumerate(tokens):
        remaining = ''.join(tokens[i+1:]) if i+1 < len(tokens) else 'ε'

        if sym in OPEN:
            stack.append(sym)
            action = f"Read '{sym}' → Push '{sym}'"

        elif sym in CLOSE:
            expected = CLOSE[sym]
            if len(stack) == 1:
                action = f"Read '{sym}' → Stack empty → REJECT"
                trace.append({'step': i+1, 'state': 'q_reject',
                               'remaining': remaining, 'stack': list(stack), 'action': action})
                return {'accepted': False, 'trace': trace,
                        'reason': f"Step {i+1}: Unmatched closing '{sym}' — stack is empty."}
            top = stack[-1]
            if top != expected:
                action = f"Read '{sym}' → Top='{top}', expected '{expected}' → REJECT"
                trace.append({'step': i+1, 'state': 'q_reject',
                               'remaining': remaining, 'stack': list(stack), 'action': action})
                return {'accepted': False, 'trace': trace,
                        'reason': f"Step {i+1}: Mismatched delimiter — read '{sym}' but top of stack is '{top}'."}
            stack.pop()
            action = f"Read '{sym}' → Pop '{top}' (match)"

        else:
            action = f"Read '{sym}' → Symbol not in alphabet {{, }}, (, ) → REJECT"
            trace.append({'step': i+1, 'state': 'q_reject',
                           'remaining': remaining, 'stack': list(stack), 'action': action})
            return {'accepted': False, 'trace': trace,
                    'reason': f"Step {i+1}: Symbol '{sym}' not in alphabet Σ = {{ {{, }}, (, ) }}."}

        trace.append({'step': i+1, 'state': 'q0', 'remaining': remaining,
                      'stack': list(stack), 'action': action})

    # end of input
    if stack == [BOTTOM]:
        trace.append({'step': len(tokens)+1, 'state': 'q_accept', 'remaining': 'ε',
                      'stack': list(stack), 'action': 'Input exhausted, stack=[$] → ACCEPT (nesting OK)'})
        return {'accepted': True, 'trace': trace, 'reason': 'All delimiters matched.'}
    else:
        leftover = ''.join(stack[1:])
        trace.append({'step': len(tokens)+1, 'state': 'q_reject', 'remaining': 'ε',
                      'stack': list(stack),
                      'action': f"Input exhausted, stack={stack} → REJECT"})
        return {'accepted': False, 'trace': trace,
                'reason': f"Input ended but unmatched opener(s) remain: '{leftover}'."}


# ─────────────────────────────────────────────
#  Phase 2 — Canonical Form Check
#  At each nesting level, { } groups must come before ( ) groups.
# ─────────────────────────────────────────────

def is_canonical(tokens: list) -> tuple:
    """
    Walks the token list and at each nesting level records the sequence
    of top-level opener types. Returns (True, '') if canonical,
    or (False, reason) if not.
    """
    # Build a tree of the structure: each level is a list of opener types
    # in the order they appear at that level.
    # We use a stack of lists; each list collects opener types at that depth.
    level_openers = [[]]   # stack of lists; level_openers[-1] = current level
    i = 0
    while i < len(tokens):
        sym = tokens[i]
        if sym in OPEN:
            # Record this opener at the current level
            level_openers[-1].append(sym)
            # Push a new level for the contents of this block
            level_openers.append([])
        elif sym in CLOSE:
            # Pop the inner level (we don't need to check it here, nesting already verified)
            level_openers.pop()
        i += 1

    # Now check canonical rule on every level that was recorded.
    # We need to re-walk and check each level's opener sequence.
    # Rule: within a level, all '{' openers must appear before any '(' opener.
    def check_sequence(openers):
        seen_paren = False
        for op in openers:
            if op == '(':
                seen_paren = True
            elif op == '{':
                if seen_paren:
                    return False, "A '{' group appears after a '(' group at the same nesting level — not canonical."
        return True, ''

    # Re-walk to collect per-level sequences properly
    stack_levels = [[]]
    for sym in tokens:
        if sym in OPEN:
            stack_levels[-1].append(sym)
            stack_levels.append([])
        elif sym in CLOSE:
            inner = stack_levels.pop()
            ok, reason = check_sequence(inner)
            if not ok:
                return False, reason
    # Check top level
    ok, reason = check_sequence(stack_levels[0])
    if not ok:
        return False, reason
    return True, ''


# ─────────────────────────────────────────────
#  Full simulate: nesting + canonical check
# ─────────────────────────────────────────────

def simulate(input_string: str) -> dict:
    tokens = list(input_string.replace(' ', ''))

    # Phase 1: proper nesting
    nest_result = simulate_nesting(tokens)
    if not nest_result['accepted']:
        return nest_result

    # Phase 2: canonical form
    ok, reason = is_canonical(tokens)
    if not ok:
        # Add a canonical-rejection step to the trace
        trace = nest_result['trace']
        trace.append({
            'step': len(tokens)+2,
            'state': 'q_reject',
            'remaining': 'ε',
            'stack': ['$'],
            'action': 'Canonical check FAILED → REJECT'
        })
        return {
            'accepted': False,
            'trace': trace,
            'reason': f"Nesting is valid but string is NOT in canonical form. {reason}"
        }

    # Both checks passed
    nest_result['reason'] = 'Properly nested AND in canonical form ({{ }} before ( ) at every level).'
    return nest_result


# ─────────────────────────────────────────────
#  Pretty Printer
# ─────────────────────────────────────────────

def print_trace(input_string: str, result: dict):
    label = "ACCEPTED ✓" if result['accepted'] else "REJECTED ✗"
    display = input_string if input_string.strip() else "(empty string ε)"
    print(f"\n{'='*65}")
    print(f"Input : {display}")
    print(f"Result: {label}")
    print(f"{'='*65}")
    print(f"{'Step':<6} {'State':<12} {'Remaining':<14} {'Stack':<22} {'Action'}")
    print('-'*85)
    for row in result['trace']:
        print(f"{row['step']:<6} {row['state']:<12} {row['remaining']:<14} {str(row['stack']):<22} {row['action']}")
    print(f"\nExplanation: {result['reason']}")


# ─────────────────────────────────────────────
#  Test Suite
# ─────────────────────────────────────────────

TEST_CASES = [
    # ── Accepted (properly nested AND canonical) ─────────────────────────
    ("",           "A1 — Empty string ε (trivially canonical)"),
    ("{}",         "A2 — Single brace pair"),
    ("()",         "A3 — Single paren pair"),
    ("{}()",       "A4 — Braces before parens at top level (canonical)"),
    ("{({})}",     "A5 — Deeply nested: braces wrap parens wrap braces"),
    ("{}{}()()",   "A6 — Multiple pairs: all braces before all parens"),
    ("{()}{}",     "A7 — Mixed nesting: brace wraps paren, then another brace"),

    # ── Rejected ─────────────────────────────────────────────────────────
    (")(},",       "R1 — Invalid symbols (only { } ( ) allowed)"),
    ("(}",         "R2 — Mismatched delimiter types"),
    ("(((",        "R3 — Incomplete input: openers never closed"),
    ("(){}",       "R4 — NOT canonical: ( ) appears before { } at top level"),
    ("{(})",       "R5 — Mismatched crossing delimiters"),
]


def run_all_tests():
    print("\n" + "█"*65)
    print("  CEN 350 — PDA Simulator")
    print("  Domain: Programming Block Syntax  |  Project Code: 12")
    print("  Constraint: Two types only ({ } and ( ))")
    print("  Feature: Accept only canonical/normalized forms")
    print("█"*65)
    for (s, desc) in TEST_CASES:
        print(f"\n▶  {desc}")
        result = simulate(s)
        print_trace(s, result)


# ─────────────────────────────────────────────
#  Interactive Mode
# ─────────────────────────────────────────────

def interactive():
    print("\n" + "="*65)
    print("  PDA Simulator — Interactive Mode")
    print("  Alphabet: { } ( )  only")
    print("  Accepted: properly nested AND { } before ( ) at every level")
    print("="*65)
    while True:
        s = input("\nInput: ").strip()
        if s.lower() in ('quit', 'exit', 'q'):
            print("Bye.")
            break
        result = simulate(s)
        print_trace(s, result)


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive()
    else:
        run_all_tests()
