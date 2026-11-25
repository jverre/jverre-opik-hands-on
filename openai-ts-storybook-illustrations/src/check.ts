import process from "node:process";

// Reads the project back over Opik's REST API and prints what landed: traces,
// the spans under them, prompt versions and attachments. Run it after `demo`.
const base = () =>
  (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api/").replace(/\/?$/, "/");

async function get(pathAndQuery: string): Promise<any> {
  const headers: Record<string, string> = {
    "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
  };
  if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;
  const res = await fetch(base() + pathAndQuery, { headers });
  if (!res.ok) throw new Error(`GET ${pathAndQuery} -> ${res.status}`);
  return res.json();
}

export async function checkProject(project: string): Promise<void> {
  const q = encodeURIComponent(project);
  const projects = await get(`v1/private/projects?name=${q}&size=5`);
  const projectId: string | undefined = projects.content?.find(
    (p: any) => p.name === project,
  )?.id;
  if (!projectId) throw new Error(`Project ${project} not found`);

  const traces = (await get(`v1/private/traces?project_id=${projectId}&size=50`)).content ?? [];
  const spans =
    (await get(`v1/private/spans?project_id=${projectId}&size=100`)).content ?? [];
  console.log(`project ${project}: ${traces.length} traces, ${spans.length} spans`);

  for (const t of traces.reverse()) {
    const span = spans.find((s: any) => s.trace_id === t.id);
    const att = await get(
      `v1/private/attachment/list?project_id=${projectId}&entity_type=trace&entity_id=${t.id}` +
        `&path=${encodeURIComponent(Buffer.from(base()).toString("base64"))}`,
    );
    const files = (att.content ?? []).map((a: any) => `${a.file_name} (${a.mime_type})`);
    console.log(
      `- ${t.name} [${(t.tags ?? []).join(", ")}] span=${span?.name}/${span?.type} tokens=${span?.usage?.total_tokens ?? "n/a"} ` +
        `cost=${span?.total_estimated_cost ?? "n/a"} attachments=${JSON.stringify(files)}`,
    );
  }

  const prompts = await get(`v1/private/prompts?name=storybook-page-brief&size=5`);
  console.log(`prompt library: ${(prompts.content ?? []).map((p: any) => `${p.name} (${p.version_count} versions)`).join(", ") || "none"}`);
}
