# Example Flows

## Example request 1

Build a main agent with subagents to audit whether our LLM support assistant can
be talked into using privileged tools.

Recommended split:

- main agent: planning and synthesis
- recon subagent: tools and auth flow
- threat-model subagent: abuse paths
- policy subagent: policy conflicts
- evidence subagent: merge outputs

## Example request 2

I want an agent-team skill for reviewing prompt injection and tool abuse in a
customer-service copilot.

Recommended deliverable:

- one `SKILL.md`
- one `agents/openai.yaml`
- references for architecture and prompt templates

## Example request 3

Teach me how to design a main agent and several subagents for a security review
workflow.

Recommended answer shape:

1. define ownership boundaries
2. define delegation rules
3. provide prompt templates
4. explain merge and final reporting
