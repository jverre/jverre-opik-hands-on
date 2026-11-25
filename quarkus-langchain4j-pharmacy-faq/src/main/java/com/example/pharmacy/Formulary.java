package com.example.pharmacy;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/** Loads the fictional formulary and splits each entry into one chunk per "## " section. */
public final class Formulary {

    /** One retrievable passage: which drug, which section, and the text itself. */
    public record Chunk(String drug, String section, String text) {
        public String label() {
            return drug + " / " + section;
        }
    }

    public static final List<String> FILES = List.of(
            "calmorex", "lumidine", "ferravel", "solvane", "tendrix", "clotavar");

    private Formulary() {
    }

    public static List<Chunk> load() {
        List<Chunk> chunks = new ArrayList<>();
        for (String name : FILES) {
            try (InputStream in = Formulary.class.getResourceAsStream("/formulary/" + name + ".md")) {
                if (in == null) {
                    throw new IllegalStateException("Missing formulary file: " + name);
                }
                chunks.addAll(split(new String(in.readAllBytes(), StandardCharsets.UTF_8)));
            } catch (IOException e) {
                throw new IllegalStateException("Cannot read formulary file " + name, e);
            }
        }
        return chunks;
    }

    static List<Chunk> split(String markdown) {
        String drug = "unknown";
        String section = null;
        StringBuilder body = new StringBuilder();
        List<Chunk> chunks = new ArrayList<>();
        for (String line : markdown.split("\n")) {
            if (line.startsWith("# ")) {
                drug = line.substring(2).trim();
            } else if (line.startsWith("## ")) {
                flush(chunks, drug, section, body);
                section = line.substring(3).trim();
            } else {
                body.append(line).append('\n');
            }
        }
        flush(chunks, drug, section, body);
        return chunks;
    }

    private static void flush(List<Chunk> chunks, String drug, String section, StringBuilder body) {
        String text = body.toString().strip();
        if (section != null && !text.isEmpty()) {
            // Repeating the drug name inside the text keeps each chunk searchable on its own.
            chunks.add(new Chunk(drug, section, drug + " - " + section + ": " + text));
        }
        body.setLength(0);
    }
}
