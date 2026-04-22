# Merge Rules

Merge findings when:

- they describe the same object selection flaw
- they use different wording for the same exploit path
- the only difference is naming

Keep findings separate when:

- one is read disclosure and one is write mutation
- one is ownership-based and one is tenant-based
- one relation failure is about selection and another is about returned object scope

Never hide uncertainty by merging a strong finding with a weak speculative note.
