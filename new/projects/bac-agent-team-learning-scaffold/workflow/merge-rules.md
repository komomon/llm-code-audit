# Merge Rules

Merge findings when:

- they describe the same unauthorized path
- they have the same sink and same missing control
- the only difference is naming

Keep findings separate when:

- one is ownership-based and one is tenant-based
- one is read-only and one is write-impacting
- one is horizontal and one is vertical privilege escalation
- the remediation differs materially

Never merge a strong finding with a weak speculative note in a way that hides uncertainty.
