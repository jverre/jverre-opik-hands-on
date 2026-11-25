import { Mastra } from "@mastra/core/mastra";
import { PinoLogger } from "@mastra/loggers";
import { LibSQLStore } from "@mastra/libsql";
import { patronAgent } from "./agents/patronAgent.ts";

export const mastra = new Mastra({
  agents: { patronAgent },
  storage: new LibSQLStore({ id: "memory-store", url: ":memory:" }),
  logger: new PinoLogger({ name: "Mastra", level: "warn" }),
});
