package com.example.pharmacy;

import io.opentelemetry.api.trace.Span;
import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;

@Path("/ask")
public class AskResource {

    @Inject
    FormularyIndex index;

    @Inject
    PharmacyAssistant assistant;

    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String ask(@QueryParam("q") String question) {
        String context = index.retrieve(question);
        String answer = assistant.answer(context, question);

        // The HTTP server span is the root of each trace. Putting the question and answer on it
        // fills the trace-level Input / Output columns in Opik's trace table.
        Span root = Span.current();
        root.setAttribute("input", question);
        root.setAttribute("output", answer);
        return answer;
    }
}
