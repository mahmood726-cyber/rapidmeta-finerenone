"""A completeness assertion has to survive the transport, not just the sender.

WHAT HAPPENED. lane_enqueue_agy2 writes a packet containing an entire canonical object and
tells the reviewer, in bold, that nothing is withheld. For two lanes that sentence was false
by the time the reviewer read it: the prompt file on disk was 487,175 bytes and complete,
and the answer came back saying

    "The provided JSON object is incomplete ... <truncated 295594 bytes>"

The vendor had cut the input. 487,175 - 295,594 = 191,581 bytes delivered, and the SAME
191,581 on both lanes -- a cap, not a hiccup.

The reviewer answered COULD NOT DETERMINE and named the gap, which is exactly what the
packet instruction asks for and the reason that instruction exists. That is the instruction
working. But it worked because the vendor happened to announce the cut. NINETEEN OTHER LANES
CARRIED PROMPTS LARGER THAN 191,581 BYTES AND ANSWERED WITHOUT MENTIONING TRUNCATION, and
whether they were cut silently is NOT DETERMINABLE from anything held here -- the canary
probe that would settle it is blocked behind a 4h31m quota. So that stays could-not-determine
and is not written down as either.

THE RULE, WHICH DOES NOT DEPEND ON SETTLING IT.

    Do not assert completeness about a packet larger than the largest packet OBSERVED to
    arrive whole.

PACKET-COMPLETENESS-2026-08-23.md said to name every field the text relies on and assert
each is present. That is a rule about ASSEMBLY. It is silent on DELIVERY, and delivery is
where these two failed. An assertion is a claim about what the reader can see, so the sender
does not get to make it alone.

THE GENERAL FORM, WHICH THIS IS THE SECOND INSTANCE OF TONIGHT. When a service tells you why
it refused, that text is DATA -- parse it, do not retry blind. The quota error names its own
reset interval and the daemon now honours it to the second rather than guessing; the
truncation notice names its own dropped byte count and that is what measured the cap here.
Both were sitting in plain text in an error nobody was reading.
"""
from __future__ import annotations

import re

# MEASURED, NOT ASSUMED. Both truncated lanes delivered exactly this many bytes. It is
# recorded as an observation with its provenance, so a later observation can move it.
OBSERVED_DELIVERED_CEILING = 191581
OBSERVED_ON = ("agy", "2026-08-24", "agy_double_rated__iv_iron_hf__acm and __hfh_recurrent",
               "vendor emitted '<truncated 295594 bytes>' on a 487,175-byte prompt")

# A margin, because the cap is measured on two samples and may be token-shaped rather than
# byte-shaped. Undersending costs a re-run; oversending costs a false completeness assertion
# and, on the evidence of this session, a manufactured defect class.
SAFE_ASSERTABLE_BYTES = 160000

TRUNCATION = re.compile(r"truncated\s+([\d,]+)\s+bytes", re.I)


def delivered_whole(packet_bytes):
    """Three states, because two of them are different kinds of no."""
    if packet_bytes <= SAFE_ASSERTABLE_BYTES:
        return "ASSERTABLE"
    if packet_bytes > OBSERVED_DELIVERED_CEILING:
        return "TOO_LARGE_TO_ASSERT"
    return "UNKNOWN_MARGIN"


def assertion_for(packet_bytes):
    """The completeness paragraph a packet of this size is ENTITLED to make.

    A packet too large to assert completeness does not get a weaker assertion -- it gets an
    HONEST one that tells the reviewer the input may have been cut and what to do about it.
    Softening the wording while keeping the claim would be the worst of the three.
    """
    state = delivered_whole(packet_bytes)
    if state == "ASSERTABLE":
        return ("PACKET COMPLETENESS, ASSERTED. Everything you need is in this message. The\n"
                "material below is reproduced IN FULL and unabridged; nothing is withheld or\n"
                "summarised. You have no file access and should not ask for any.\n\n"
                "If something you need is genuinely not here, answer COULD NOT DETERMINE and\n"
                "NAME what is missing. Do NOT say anything is fabricated, invented, or absent\n"
                "from the record: an earlier blinded read of a partial packet returned six\n"
                "confident accusations of fabrication, and all six named facts that were\n"
                "present in the record and missing only from the packet. A false accusation\n"
                "costs as much here as a missed defect.\n\n")
    return ("PACKET COMPLETENESS CANNOT BE ASSERTED FOR THIS ONE, AND YOU ARE BEING TOLD SO\n"
            "RATHER THAN REASSURED. This message is %d bytes. Packets above roughly %d bytes\n"
            "have been observed arriving CUT, with the tail silently removed before you see\n"
            "it. What was SENT is complete. What ARRIVED may not be.\n\n"
            "So: if a field you need is not here, the correct answer is COULD NOT DETERMINE,\n"
            "NAMING the field. Do NOT conclude it is missing from the record, and do NOT call\n"
            "anything fabricated -- an earlier blinded read of a partial packet returned six\n"
            "confident accusations of fabrication and all six named facts that were in the\n"
            "record and missing only from the packet. If you can see a marker saying input\n"
            "was truncated, say so in your first line and stop; that answer is more useful\n"
            "than one written over a hole.\n\n" % (packet_bytes, OBSERVED_DELIVERED_CEILING))


def output_is_trustworthy(text):
    """A returned answer written over a truncated input is not a result.

    Returns (ok, dropped_bytes_or_None). A harvester that counts these as findings is
    counting the transport's damage as the corpus's.
    """
    m = TRUNCATION.search(text or "")
    if m:
        return False, int(m.group(1).replace(",", ""))
    return True, None
