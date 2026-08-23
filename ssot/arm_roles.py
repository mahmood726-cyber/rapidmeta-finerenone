"""Which arm is the treatment. Read from `role`, NEVER derived from position or label order.

THE ARCHITECTURE THAT WORKED WITHOUT ANYONE NOTICING IT WAS WORKING.

Three scripts determine the treatment arm by sorting arm labels lexicographically and taking
the first -- `arms = sorted(per_arm.keys()); tN = arms[0]`. `BG_CONTROL` sorts before
`BG_EXPERIMENTAL`, so every effect built that way inverts, and this project has already
published an object saying empagliflozin was worse than placebo from exactly this class.

IT HAS NEVER BITTEN THE STORED CORPUS, and the reason is structural rather than lucky in the
way that matters: the objects store arms as a LIST WITH AN EXPLICIT ROLE.

    "arms": [{"label": "dapagliflozin 10 mg once daily", "role": "treatment",
              "events": 386, "participants": 2373},
             {"label": "placebo", "role": "control", "events": 502, "participants": 2371}]

DIRECTION IS RECORDED, NOT INFERRED. A sweep of 155 objects and 407 trials found ZERO trials
whose first arm label sorts as a control or placebo -- the mechanism has never been handed the
input it needs. That is the only structural protection in this repository that was working
silently, and it is written down here so that a later "simplification" to a label-keyed map
does not remove it without anyone realising what it was for.

TWO ARMS CAN BOTH BE TREATMENT. PURPOSE-1 (NCT04994509) stores lenacapavir and F/TAF both as
`role: "treatment"` with no control arm, and carries four distinct contrasts. Any caller that
assumes exactly one treatment and one control will mis-pair that trial, which is how a
first-element read produced two false inversion reports. `roles()` returns what is there.
"""

TREATMENT = ("treat", "exper", "interv", "active")
CONTROL = ("control", "placebo", "comparator", "usual", "standard", "sham")


def roles(arms):
    """-> (treatment_arms, control_arms, unlabelled). Never guesses from order."""
    t, c, u = [], [], []
    if isinstance(arms, dict):
        arms = [dict(v, label=k) if isinstance(v, dict) else {"label": k} for k, v in arms.items()]
    for a in (arms or []):
        if not isinstance(a, dict):
            continue
        r = str(a.get("role") or "").strip().lower()
        if r.startswith(TREATMENT):
            t.append(a)
        elif r.startswith(CONTROL):
            c.append(a)
        else:
            u.append(a)
    return t, c, u


def the_pair(arms):
    """The single treatment/control pair, or None when the trial is not that shape.

    RETURNS None RATHER THAN A GUESS for a trial with two treatments and no control, or with
    unlabelled arms. A caller that needs a pair must handle not getting one; inventing it is
    how a four-contrast trial becomes one wrong number.
    """
    t, c, u = roles(arms)
    if len(t) == 1 and len(c) == 1 and not u:
        return t[0], c[0]
    return None


def refuse_positional(arms, where):
    """Raise if a caller is about to take an arm by position or sorted label."""
    t, c, u = roles(arms)
    if t and c:
        return
    raise ValueError(
        "REFUSED: %s cannot determine the treatment arm -- %d labelled treatment, %d control, "
        "%d unlabelled. Read `role`; do not sort labels. `BG_CONTROL` sorts before "
        "`BG_EXPERIMENTAL` and the effect inverts." % (where, len(t), len(c), len(u)))
