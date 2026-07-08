from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import google.generativeai as genai
from PIL import Image
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
BRANDING_DIR = APP_DIR / "assets" / "branding"
MEDIA_DIR = APP_DIR / "assets" / "media"
SIDEBAR_LOGO_PATH = BRANDING_DIR / "logo_white.jpg"
DEFAULT_STORAGE_TIP = "Refrigerate fresh food quickly, label leftovers, and freeze anything you will not use within 2 to 3 days."
DEFAULT_WASTE_TIP = "Plan one flexible meal each week to use leftovers, soft vegetables, and herbs before they spoil."
PLACEHOLDER_KEY_SNIPPETS = ("paste-your", "your-google-ai-api-key")
PANTRY_STORAGE_GUIDE = {
    "tomato": ("Counter or fridge", "Use within 3-5 days", "Roast or blend into soup when very ripe."),
    "banana": ("Counter", "Use within 2-6 days", "Freeze slices for smoothies or pancakes."),
    "bread": ("Bread box or freezer", "Use within 3-4 days", "Turn stale slices into croutons or toast."),
    "milk": ("Refrigerator", "Use within 5-7 days after opening", "Use extra milk in sauces, oats, or pancakes."),
    "cheese": ("Refrigerator", "Use within 1-3 weeks after opening", "Grate and freeze for later cooking."),
    "egg": ("Refrigerator", "Use within 3-5 weeks", "Hard-boil older eggs for quick snacks."),
    "potato": ("Cool dark place", "Use within 2-4 weeks", "Roast extras for meal prep."),
    "onion": ("Cool dry place", "Use within 2-4 weeks", "Caramelize and store portions for later meals."),
    "spinach": ("Refrigerator", "Use within 2-4 days", "Blend wilted leaves into soups or omelets."),
    "rice": ("Airtight pantry container", "Use within 6-12 months", "Cook extra and turn it into fried rice."),
}

FALLBACK_RECIPE_STYLES = {
    "Quick": "Make a fast skillet toss with olive oil, garlic, your ingredients, and a finishing squeeze of lemon.",
    "Comfort": "Turn the ingredients into a warm bowl meal with a broth, sauce, or grain base.",
    "Healthy": "Build a balanced plate with lean protein, vegetables, and a light seasoning blend.",
    "Snack": "Combine the ingredients into a toast, wrap, or bowl with one crunchy topping.",
}


st.set_page_config(
    page_title="Gastronomix AI",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    .hero {
        padding: 1.6rem;
        border-radius: 24px;
        background: linear-gradient(135deg, #102a43 0%, #243b53 55%, #486581 100%);
        color: white;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.20);
        margin-bottom: 1rem;
    }
    .hero h1 {margin: 0 0 0.4rem 0; font-size: 2.4rem;}
    .hero p {margin: 0; color: rgba(255,255,255,0.88);}
    .panel {
        background: rgba(255,255,255,0.72);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 20px;
        padding: 1rem;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    }
    .badge {
        display: inline-block;
        padding: 0.3rem 0.7rem;
        margin: 0.2rem 0.35rem 0.2rem 0;
        border-radius: 999px;
        background: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
        font-size: 0.92rem;
        font-weight: 600;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def init_state() -> None:
    defaults = {
        "pantry_items": [],
        "analysis": None,
        "analysis_note": "",
        "recipe_markdown": "",
        "recipe_note": "",
        "history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def get_secret(name: str) -> str:
    try:
        secret_value = st.secrets.get(name, "")
    except Exception:
        secret_value = ""
    return str(secret_value or os.getenv(name, "")).strip()


def get_model() -> tuple[Any | None, str | None]:
    api_key = get_secret("GOOGLE_API_KEY")
    if not is_configured_api_key(api_key):
        return None, "Add GOOGLE_API_KEY to .streamlit/secrets.toml to enable live AI analysis."

    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-1.5-flash"), None
    except Exception as exc:  # pragma: no cover - network/service setup
        return None, f"Gemini setup failed: {exc}"


def call_model(parts: list[Any]) -> tuple[str | None, str | None]:
    model, error = get_model()
    if error:
        return None, error

    try:
        response = model.generate_content(parts)
        text = (getattr(response, "text", "") or "").strip()
        if not text:
            return None, "The AI service returned an empty response."
        return text, None
    except Exception as exc:  # pragma: no cover - network/service execution
        return None, f"The AI service is temporarily unavailable: {exc}"


def strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def is_configured_api_key(api_key: str) -> bool:
    lowered_key = api_key.lower()
    return bool(api_key and not any(snippet in lowered_key for snippet in PLACEHOLDER_KEY_SNIPPETS))


def parse_json_payload(text: str) -> dict[str, Any]:
    cleaned = strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def normalize_items(raw_items: Any) -> list[str]:
    if isinstance(raw_items, str):
        candidates = [item.strip() for item in raw_items.split(",")]
    elif isinstance(raw_items, list):
        candidates = [str(item).strip() for item in raw_items]
    else:
        candidates = []

    seen: set[str] = set()
    items: list[str] = []
    for candidate in candidates:
        if not candidate:
            continue
        key = candidate.lower()
        if key not in seen:
            seen.add(key)
            items.append(candidate.title())
    return items


def fallback_analysis() -> dict[str, Any]:
    return {
        "items": [],
        "meal_type": "Unknown",
        "confidence": "Unavailable",
        "storage_tip": DEFAULT_STORAGE_TIP,
        "waste_reduction_tip": DEFAULT_WASTE_TIP,
        "recipe_seed": [],
    }


def analyze_food_image(image: Image.Image) -> tuple[dict[str, Any], str | None]:
    prompt = """
    You are a food recognition assistant.
    Analyze the food in this image and return strict JSON with this schema only:
    {
      "items": ["ingredient 1", "ingredient 2"],
      "meal_type": "short label",
      "confidence": "High|Medium|Low",
      "storage_tip": "one sentence",
      "waste_reduction_tip": "one sentence",
      "recipe_seed": ["dish idea 1", "dish idea 2"]
    }
    Only include food items you are reasonably confident about.
    """.strip()

    response_text, error = call_model([prompt, image])
    if error:
        return fallback_analysis(), error

    try:
        payload = parse_json_payload(response_text)
        analysis = {
            "items": normalize_items(payload.get("items", [])),
            "meal_type": str(payload.get("meal_type", "Unknown")).strip() or "Unknown",
            "confidence": str(payload.get("confidence", "Medium")).strip() or "Medium",
            "storage_tip": str(payload.get("storage_tip", DEFAULT_STORAGE_TIP)).strip() or DEFAULT_STORAGE_TIP,
            "waste_reduction_tip": str(payload.get("waste_reduction_tip", DEFAULT_WASTE_TIP)).strip() or DEFAULT_WASTE_TIP,
            "recipe_seed": normalize_items(payload.get("recipe_seed", [])),
        }
        return analysis, None
    except Exception:
        fallback = fallback_analysis()
        return fallback, "Image analysis completed, but the response could not be fully parsed."


def build_fallback_recipe(ingredients: list[str], cuisine: str, goal: str, max_minutes: int) -> str:
    joined = ", ".join(ingredients) if ingredients else "your available pantry items"
    style = FALLBACK_RECIPE_STYLES.get(goal, FALLBACK_RECIPE_STYLES["Quick"])
    return f"""
## Pantry Recipe Starter

**Style:** {goal} · **Cuisine:** {cuisine} · **Time:** ~{max_minutes} minutes

Use **{joined}** as your base. {style}
Keep the flavors aligned with a **{cuisine}** direction and aim to finish within **{max_minutes} minutes**.

### Suggested flow
1. Prep the ingredients and group quick-cooking items together.
2. Start with aromatics or seasoning, then add your main ingredients.
3. Finish with a sauce, broth, yogurt, citrus, or herbs for balance.
4. Save leftovers in an airtight container for the next meal.

### Easy upgrades
- Add a protein if you need a fuller meal.
- Use rice, pasta, toast, or greens as a base.
- Finish with seeds, nuts, or herbs for texture.
""".strip()


def generate_recipe(ingredients: list[str], cuisine: str, goal: str, max_minutes: int) -> tuple[str, str | None]:
    if not ingredients:
        return "Add a few pantry items or detect ingredients from an image to generate a recipe.", None

    prompt = f"""
    Create one modern home-cooking recipe in markdown.
    Constraints:
    - Ingredients to prioritize: {', '.join(ingredients)}
    - Cuisine direction: {cuisine}
    - Meal goal: {goal}
    - Max time: {max_minutes} minutes
    - Format with these sections only: Recipe Name, Why It Works, Ingredients, Steps, Smart Swaps, Storage Tip
    - Keep the recipe realistic for a home kitchen and reduce food waste when possible.
    """.strip()

    response_text, error = call_model([prompt])
    if error:
        return build_fallback_recipe(ingredients, cuisine, goal, max_minutes), error
    return response_text, None


def add_to_pantry(items: list[str]) -> None:
    existing = {item.lower() for item in st.session_state.pantry_items}
    for item in items:
        if item.lower() not in existing:
            st.session_state.pantry_items.append(item)
            existing.add(item.lower())


def pantry_table(items: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in items:
        advice = PANTRY_STORAGE_GUIDE.get(item.lower(), ("Cool, dry place or fridge", "Use soon", DEFAULT_WASTE_TIP))
        rows.append(
            {
                "Item": item,
                "Best storage": advice[0],
                "Use by": advice[1],
                "Low-waste tip": advice[2],
            }
        )
    return rows


def render_badges(items: list[str]) -> None:
    if not items:
        st.caption("No items detected yet.")
        return
    badges = "".join(f'<span class="badge">{item}</span>' for item in items)
    st.markdown(badges, unsafe_allow_html=True)


with st.sidebar:
    if SIDEBAR_LOGO_PATH.exists():
        st.image(str(SIDEBAR_LOGO_PATH), use_container_width=True)

    st.markdown("### App status")
    configured_api_key = get_secret("GOOGLE_API_KEY")
    if is_configured_api_key(configured_api_key):
        st.success("AI features are configured.")
    else:
        st.info("Running in graceful fallback mode until a Google API key is added.")

    st.markdown("### Pantry quick add")
    quick_add = st.text_input("Add items", placeholder="milk, spinach, rice")
    if st.button("Add to pantry", use_container_width=True):
        new_items = normalize_items(quick_add)
        if new_items:
            add_to_pantry(new_items)
            st.success(f"Added {len(new_items)} item(s) to the pantry.")
        else:
            st.warning("Enter at least one pantry item.")

    if (MEDIA_DIR / "Gastronomix AI.mp4").exists():
        with st.expander("Preview demo"):
            st.video(str(MEDIA_DIR / "Gastronomix AI.mp4"))

hero_left, hero_right = st.columns([1.5, 1])
with hero_left:
    st.markdown(
        """
        <div class="hero">
            <h1>🍽️ Gastronomix AI</h1>
            <p>Recognize ingredients, build a smarter pantry, and turn leftovers into practical recipes with graceful AI fallbacks.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hero_right:
    st.markdown(
        """
        <div class="panel">
            <strong>What’s improved</strong>
            <ul>
                <li>Modernized Streamlit layout and theme</li>
                <li>Single-key AI setup through <code>secrets.toml</code></li>
                <li>Fallback recipe generation when AI is unavailable</li>
                <li>Pantry tracking, storage guidance, and better error handling</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption("Tip: add your Google AI API key to the Streamlit secrets file for live vision and recipe generation.")

food_tab, recipe_tab, pantry_tab = st.tabs(["Food Vision", "Recipe Studio", "Pantry Board"])

with food_tab:
    st.subheader("Recognize food from a photo")
    source = st.radio("Choose an image source", ["Upload image", "Use camera"], horizontal=True)
    image_input = st.file_uploader("Upload a food image", type=["jpg", "jpeg", "png"]) if source == "Upload image" else st.camera_input("Take a food photo")

    if st.button("Analyze image", type="primary"):
        if image_input is None:
            st.warning("Upload or capture an image first.")
        else:
            try:
                image = Image.open(image_input).convert("RGB")
                with st.spinner("Analyzing your ingredients..."):
                    analysis, note = analyze_food_image(image)
                st.session_state.analysis = analysis
                st.session_state.analysis_note = note or ""
                st.session_state.history.insert(0, {"source": source, "items": analysis["items"]})
                st.image(image, caption="Selected image", use_container_width=True)
            except Exception as exc:
                st.error(f"The image could not be processed: {exc}")

    analysis = st.session_state.analysis
    if analysis:
        metric_a, metric_b, metric_c = st.columns(3)
        metric_a.metric("Detected items", len(analysis["items"]))
        metric_b.metric("Meal type", analysis["meal_type"])
        metric_c.metric("Confidence", analysis["confidence"])
        render_badges(analysis["items"])

        col1, col2 = st.columns(2)
        col1.info(analysis["storage_tip"])
        col2.success(analysis["waste_reduction_tip"])

        if analysis["recipe_seed"]:
            st.markdown("**Dish ideas**")
            render_badges(analysis["recipe_seed"])

        if analysis["items"] and st.button("Add detected items to pantry"):
            add_to_pantry(analysis["items"])
            st.success("Detected items added to your pantry board.")

        if st.session_state.analysis_note:
            st.info(st.session_state.analysis_note)

with recipe_tab:
    st.subheader("Generate a recipe from what you already have")
    default_ingredients = ", ".join(st.session_state.pantry_items)
    ingredient_text = st.text_area(
        "Ingredients",
        value=default_ingredients,
        placeholder="tomato, bread, cheese",
        help="Use pantry items, detected items, or type your own ingredients.",
    )

    recipe_col1, recipe_col2, recipe_col3 = st.columns(3)
    cuisine = recipe_col1.selectbox("Cuisine", ["Global", "Indian", "Italian", "Asian", "Mediterranean", "Mexican"])
    goal = recipe_col2.selectbox("Meal goal", ["Quick", "Healthy", "Comfort", "Snack"])
    max_minutes = recipe_col3.slider("Max time (minutes)", min_value=10, max_value=60, value=25, step=5)

    if st.button("Generate recipe", type="primary"):
        ingredients = normalize_items(ingredient_text)
        with st.spinner("Designing a practical recipe..."):
            recipe_markdown, recipe_note = generate_recipe(ingredients, cuisine, goal, max_minutes)
        st.session_state.recipe_markdown = recipe_markdown
        st.session_state.recipe_note = recipe_note or ""

    if st.session_state.recipe_markdown:
        st.markdown(st.session_state.recipe_markdown)
    if st.session_state.recipe_note:
        st.info(st.session_state.recipe_note)

with pantry_tab:
    st.subheader("Track ingredients and reduce waste")
    pantry_items = st.session_state.pantry_items

    stats_col1, stats_col2 = st.columns(2)
    stats_col1.metric("Pantry items", len(pantry_items))
    stats_col2.metric("Recent detections", len(st.session_state.history))

    render_badges(pantry_items)

    if pantry_items:
        st.dataframe(pantry_table(pantry_items), use_container_width=True, hide_index=True)
        if st.button("Clear pantry board"):
            st.session_state.pantry_items = []
            st.success("Pantry board cleared.")
    else:
        st.info("Your pantry board is empty. Add items from the sidebar or detect them from an image.")

    if st.session_state.history:
        with st.expander("Recent detection history"):
            for entry in st.session_state.history[:5]:
                detected = ", ".join(entry["items"]) if entry["items"] else "No confident items detected"
                st.write(f"- {entry['source']}: {detected}")
