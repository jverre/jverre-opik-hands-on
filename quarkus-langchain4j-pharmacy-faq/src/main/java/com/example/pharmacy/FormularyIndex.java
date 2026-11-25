package com.example.pharmacy;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingSearchRequest;
import dev.langchain4j.store.embedding.EmbeddingMatch;
import dev.langchain4j.store.embedding.inmemory.InMemoryEmbeddingStore;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import jakarta.inject.Inject;

import java.util.List;

/** In-memory vector index over the formulary, built once at startup with OpenAI embeddings. */
@ApplicationScoped
public class FormularyIndex {

    static final int TOP_K = 3;

    @Inject
    EmbeddingModel embeddingModel;

    @Inject
    Tracer tracer;

    private final ObjectMapper mapper = new ObjectMapper();
    private final InMemoryEmbeddingStore<TextSegment> store = new InMemoryEmbeddingStore<>();

    void onStart(@Observes StartupEvent event) {
        List<Formulary.Chunk> chunks = Formulary.load();
        List<TextSegment> segments = chunks.stream()
                .map(c -> TextSegment.from(c.text(), dev.langchain4j.data.document.Metadata.from("source", c.label())))
                .toList();
        // Startup indexing gets its own span, so its embedding call shows up in Opik as one
        // "index_formulary" trace instead of an anonymous embeddings request.
        Span span = tracer.spanBuilder("index_formulary").startSpan();
        try (Scope ignored = span.makeCurrent()) {
            List<Embedding> embeddings = embeddingModel.embedAll(segments).content();
            store.addAll(embeddings, segments);
            span.setAttribute("input", chunks.size() + " formulary chunks");
            span.setAttribute("output", "indexed " + embeddings.size() + " embeddings");
        } finally {
            span.end();
        }
    }

    /** Returns the best passages for a question, as one block of context for the prompt. */
    public String retrieve(String question) {
        // Quarkus does not trace retrieval for us, so this hand-made span makes the vector search
        // visible in Opik: its input is the query, its output the chunks that were fetched.
        // Without it, a wrong answer cannot be blamed on retrieval or on generation.
        Span span = tracer.spanBuilder("retrieve_formulary").startSpan();
        try (Scope ignored = span.makeCurrent()) {
            Embedding query = embeddingModel.embed(question).content();
            List<EmbeddingMatch<TextSegment>> matches = store.search(EmbeddingSearchRequest.builder()
                    .queryEmbedding(query).maxResults(TOP_K).build()).matches();

            ObjectNode input = mapper.createObjectNode().put("query", question).put("top_k", TOP_K);
            ObjectNode output = mapper.createObjectNode();
            ArrayNode docs = output.putArray("documents");
            StringBuilder context = new StringBuilder();
            for (EmbeddingMatch<TextSegment> m : matches) {
                docs.addObject()
                        .put("source", m.embedded().metadata().getString("source"))
                        .put("score", Math.round(m.score() * 1000) / 1000.0)
                        .put("text", m.embedded().text());
                context.append("- [").append(m.embedded().metadata().getString("source")).append("] ")
                        .append(m.embedded().text()).append('\n');
            }
            // "input" / "output" are the attribute names Opik maps onto the span's Input and Output panels.
            span.setAttribute("input", json(input));
            span.setAttribute("output", json(output));
            return context.toString();
        } finally {
            span.end();
        }
    }

    private String json(ObjectNode node) {
        try {
            return mapper.writeValueAsString(node);
        } catch (JsonProcessingException e) {
            return node.toString();
        }
    }
}
