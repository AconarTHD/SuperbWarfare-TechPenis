package com.atsuishio.superbwarfare.compat;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;

/** Pack content policy; registry entries and saved inventories remain intact. */
public final class MilitaryContentPolicy {
    private static final JsonObject PROFILE = load();
    private static final Set<String> ITEMS = entries("blocked_items");
    private static final Set<String> ENTITIES = entries("blocked_entities");
    private static final Set<String> RECIPES = entries("blocked_recipe_ids");
    public static final Set<String> ITEM_TAGS = Set.copyOf(entries("blocked_item_tags"));

    private MilitaryContentPolicy() {}

    private static JsonObject load() {
        var input = MilitaryContentPolicy.class.getResourceAsStream("/techpenis/military_profile.json");
        if (input == null) throw new IllegalStateException("Missing TechPenis military profile");
        try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader).getAsJsonObject();
        } catch (java.io.IOException exception) {
            throw new IllegalStateException("Cannot read TechPenis military profile", exception);
        }
    }

    private static Set<String> entries(String key) {
        Set<String> result = new HashSet<>();
        for (JsonElement value : PROFILE.getAsJsonArray(key)) result.add(value.getAsString());
        return result;
    }

    public static boolean blocksItem(String id) { return ITEMS.contains(id); }
    public static boolean blocksEntity(String id) { return ENTITIES.contains(id); }

    private static boolean containsBlockedItem(JsonElement value) {
        if (value == null || value.isJsonNull()) return false;
        if (value.isJsonPrimitive() && value.getAsJsonPrimitive().isString()) {
            String id = value.getAsString();
            return blocksItem(id) || id.startsWith("#") && ITEM_TAGS.contains(id.substring(1));
        }
        if (value.isJsonArray()) {
            for (JsonElement element : value.getAsJsonArray()) if (containsBlockedItem(element)) return true;
        } else if (value.isJsonObject()) {
            JsonElement tag = value.getAsJsonObject().get("tag");
            if (tag != null && tag.isJsonPrimitive() && tag.getAsJsonPrimitive().isString()
                    && ITEM_TAGS.contains(tag.getAsString())) return true;
            for (var entry : value.getAsJsonObject().entrySet()) if (containsBlockedItem(entry.getValue())) return true;
        }
        return false;
    }

    public static boolean blocksRecipe(String id, JsonElement value) {
        if (RECIPES.contains(id)) return true;
        if (id.startsWith("superbwarfare:")) return containsBlockedItem(value);
        if (!value.isJsonObject()) return false;
        JsonObject recipe = value.getAsJsonObject();
        for (String key : new String[]{"result", "results", "output", "outputs"}) {
            if (containsBlockedItem(recipe.get(key))) return true;
        }
        return false;
    }
}
