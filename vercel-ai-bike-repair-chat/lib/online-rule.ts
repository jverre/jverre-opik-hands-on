import { Opik } from "opik";
import { PROJECT_NAME } from "./telemetry";

export const RULE_NAME = "actionable_workshop_advice";
export const SCORE_NAME = "actionable_advice";

/**
 * The judge prompt. {{question}} and {{answer}} are filled from the trace's
 * input and output by the `variables` mapping below.
 */
export const JUDGE_PROMPT = `A rider asked a community bike workshop's assistant for help.

Conversation sent to the assistant (JSON):
{{question}}

Assistant reply (JSON):
{{answer}}

Return true only if the reply gives the rider something concrete to act on for a
bicycle problem: a likely cause, a check, a repair step, a price, or a clear
"stop riding and bring it in" instruction. Return false if the reply is vague,
evasive, or does not deal with a bicycle problem at all.`;

/**
 * Creates (once) the project and an LLM-as-judge online evaluation rule on it.
 * The rule runs server-side on every new trace in the project and writes the
 * `actionable_advice` feedback score, so it must exist BEFORE traffic arrives.
 * Idempotent: an existing rule with the same name is left untouched.
 */
export async function ensureOnlineRule(client: Opik): Promise<{ projectId: string; created: boolean }> {
  const api = client.api;

  // Rules attach to a project id, so make sure the project exists first.
  const found = await api.projects.findProjects({ name: PROJECT_NAME });
  let project = found.content?.find((p) => p.name === PROJECT_NAME);
  if (!project) {
    await api.projects.createProject({ name: PROJECT_NAME });
    project = (await api.projects.findProjects({ name: PROJECT_NAME })).content?.find((p) => p.name === PROJECT_NAME);
  }
  if (!project?.id) throw new Error(`Could not find or create project ${PROJECT_NAME}`);

  const existing = await api.automationRuleEvaluators.findEvaluators({ projectId: project.id, name: RULE_NAME, size: 20 });
  if (existing.content?.some((r) => r.name === RULE_NAME)) return { projectId: project.id, created: false };

  await api.automationRuleEvaluators.createAutomationRuleEvaluator({
    type: "llm_as_judge",
    action: "evaluator",
    name: RULE_NAME,
    projectIds: [project.id],
    samplingRate: 1, // score every trace; lower it for busy production projects
    enabled: true,
    code: {
      // The judge runs with the OpenAI key stored in Opik's LLM provider settings.
      model: { name: "gpt-4o-mini", temperature: 0 },
      messages: [{ role: "USER", content: JUDGE_PROMPT }],
      variables: { question: "input", answer: "output" },
      schema: [{ name: SCORE_NAME, type: "BOOLEAN", description: "Reply gives concrete, bicycle-relevant guidance" }],
    },
  });
  return { projectId: project.id, created: true };
}
