package com.example.pharmacy;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.V;
import io.quarkiverse.langchain4j.RegisterAiService;

/**
 * The model-facing half of the bot. Quarkus wraps every call to this interface in a
 * langchain4j.aiservices.PharmacyAssistant.answer span, with the OpenAI request as a child span.
 */
@RegisterAiService
public interface PharmacyAssistant {

    @SystemMessage("""
            You are the medication-information assistant for Harbourlight Pharmacy.
            Answer ONLY from the formulary excerpts you are given. If the excerpts do not
            cover the question, say the formulary has no information on it.
            Never recommend a personal dose, never say a combination is safe for a specific
            person, and never diagnose. Keep answers to three sentences or fewer, and always
            end by telling the customer to confirm with a pharmacist.
            """)
    @UserMessage("""
            Formulary excerpts:
            {context}

            Customer question: {question}
            """)
    String answer(@V("context") String context, @V("question") String question);
}
