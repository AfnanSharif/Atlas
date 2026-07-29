from __future__ import annotations

import base64
import html
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from travel_itinerary.models import TripRequest
from travel_itinerary.feedback import VisualFeedbackStore
from travel_itinerary.providers import create_image_provider, create_prompt_refiner
from travel_itinerary.service import TravelService


@st.cache_resource(show_spinner=False)
def _visual_service(image_provider_name: str, prompt_refiner_name: str, feedback_path: str) -> TravelService:
    return TravelService(
        image_provider=create_image_provider(image_provider_name),
        prompt_refiner=create_prompt_refiner(prompt_refiner_name),
        feedback_store=VisualFeedbackStore(feedback_path),
    )

st.set_page_config(page_title="Atlas AI · Itinerary Studio", page_icon="🧭", layout="wide")
st.markdown("""<style>
@keyframes glow{0%,100%{filter:hue-rotate(0deg)}50%{filter:hue-rotate(24deg)}}
.stApp{background:radial-gradient(circle at 80% 5%,#183b5b 0,transparent 34%),#07111f;color:#eef6ff}
.hero{padding:2.4rem;border:1px solid #ffffff24;border-radius:28px;background:linear-gradient(135deg,#11263dcc,#153f52aa);animation:glow 8s ease-in-out infinite}
.eyebrow{color:#ffd166;letter-spacing:.18em;font-weight:700}.day{border-left:3px solid #55d6be;padding:.4rem 1rem;margin:1rem 0}.muted{color:#a9bfd2}
[data-testid="stSidebar"]{background:#091827} div.stButton>button{border-radius:99px;background:#ffd166;color:#07111f;border:0;font-weight:700}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
</style><div class="hero"><div class="eyebrow">ATLAS AI</div><h1>Turn preferences into a trip worth remembering.</h1><p class="muted">Constraint-aware plans and art-ready prompts. Local by default, generative when you want it.</p></div>""", unsafe_allow_html=True)

service = TravelService()
with st.sidebar:
    st.header("Trip canvas")
    destination = st.selectbox("Destination", list(service.catalog.destinations) + ["Other…"])
    if destination == "Other…":
        destination = st.text_input("City or region", "Reykjavík")
    days = st.slider("Days", 1, 10, 3)
    travelers = st.selectbox("Travel party", ["solo", "couple", "family", "friends"])
    pace = st.segmented_control("Pace", ["relaxed", "balanced", "packed"], default="balanced")
    budget = st.select_slider("Budget", ["budget", "mid-range", "luxury"], value="mid-range")
    themes = st.multiselect("Interests", ["culture", "food", "nature", "art", "history", "adventure", "photography", "wellness", "family"], ["culture", "food"])
    season = st.selectbox("Season", ["spring", "summer", "autumn", "winter"])
    start = st.date_input("Start date", value=date.today())
    accessible = st.checkbox("Prioritize step-free activities")
    provider_options = ["placeholder", "diffusion"]
    configured_provider = os.getenv("IMAGE_PROVIDER", "placeholder").lower()
    image_provider_name = st.selectbox("Visual provider", provider_options, index=provider_options.index(configured_provider) if configured_provider in provider_options else 0)
    refiner_options = ["none", "gemini"]
    configured_refiner = os.getenv("PROMPT_REFINER", "none").lower()
    prompt_refiner_name = st.selectbox("Prompt refinement", refiner_options, index=refiner_options.index(configured_refiner) if configured_refiner in refiner_options else 0)
    edit_instruction = st.text_input(
        "Optional InstructPix2Pix enhancement",
        value=os.getenv("VISUAL_EDIT_INSTRUCTION", ""),
        placeholder="Warmer golden-hour light; keep landmarks unchanged",
        disabled=image_provider_name != "diffusion",
    )
    generate = st.button("Build my itinerary", use_container_width=True)

if generate:
    try:
        request = TripRequest(destination=destination, days=days, travelers=travelers, themes=tuple(themes or ["culture"]), pace=pace or "balanced", budget=budget, season=season, start_date=start, accessibility=accessible)
        st.session_state.itinerary = service.create(request)
        st.session_state.visual_cache = {}
    except ValueError as exc:
        st.error(str(exc))

itinerary = st.session_state.get("itinerary")
if itinerary:
    st.subheader(itinerary.destination)
    st.caption(f"{itinerary.summary} · {itinerary.traveler_profile}")
    tabs = st.tabs([f"Day {day.day}" for day in itinerary.days])
    try:
        feedback_path = Path(os.getenv("FEEDBACK_DB", ".local/visual-feedback.db"))
        if not feedback_path.is_absolute():
            feedback_path = ROOT / feedback_path
        visual_service = _visual_service(image_provider_name, prompt_refiner_name, str(feedback_path))
    except (ValueError, RuntimeError) as exc:
        visual_service = None
        st.error(f"Visual provider is unavailable: {exc}")
    for tab, day in zip(tabs, itinerary.days):
        with tab:
            left, right = st.columns([1.25, 1])
            with left:
                st.markdown(f"### {day.title}")
                st.caption(f"{day.date or 'Flexible date'} · {day.neighborhood_focus} · {day.estimated_cost}")
                for item in day.activities:
                    a = item.activity
                    safe_start = html.escape(item.start)
                    safe_end = html.escape(item.end)
                    safe_name = html.escape(a.name)
                    safe_description = html.escape(a.description)
                    safe_neighborhood = html.escape(a.neighborhood)
                    safe_tip = html.escape(a.tip)
                    st.markdown(f"<div class='day'><b>{safe_start}–{safe_end} · {safe_name}</b><br>{safe_description}<br><span class='muted'>{safe_neighborhood} · {a.duration_hours:g}h · {safe_tip}</span></div>", unsafe_allow_html=True)
            with right:
                shown_prompt = day.visual_prompt
                cache = st.session_state.setdefault("visual_cache", {})
                cache_key = f"{itinerary.destination}|{day.day}|{image_provider_name}|{prompt_refiner_name}|{edit_instruction}"
                render_clicked = st.button("Generate / refresh visual", key=f"render-{day.day}", use_container_width=True)
                should_render = render_clicked or (image_provider_name == "placeholder" and cache_key not in cache)
                if visual_service and should_render:
                    try:
                        with st.spinner("Rendering the personalized scene…"):
                            cache[cache_key] = visual_service.render_visual(day, itinerary.destination, edit_instruction)
                    except Exception as exc:
                        st.error(f"Could not render this visual: {exc}")
                if cache_key in cache:
                    shown_prompt, visual = cache[cache_key]
                    if isinstance(visual, str):
                        encoded = base64.b64encode(visual.encode("utf-8")).decode("ascii")
                        st.image(f"data:image/svg+xml;base64,{encoded}")
                    else:
                        st.image(visual, use_container_width=True)
                    rating = st.select_slider("Visual rating", options=[1, 2, 3, 4, 5], value=4, key=f"rating-{day.day}")
                    feedback_note = st.text_input("What should future visuals favor?", key=f"feedback-{day.day}", placeholder="More warm light and local street detail")
                    if st.button("Save feedback", key=f"save-feedback-{day.day}"):
                        visual_service.record_visual_feedback(itinerary.destination, day, shown_prompt, rating, feedback_note)
                        st.success("Saved. Positive feedback will refine future prompts for this destination.")
                with st.expander("Image-generation prompt"):
                    st.code(shown_prompt)
    for note in itinerary.planning_notes:
        st.info(note)
    payload = json.dumps(itinerary.to_dict(), indent=2, ensure_ascii=False)
    st.download_button("Download itinerary JSON", payload, f"{itinerary.destination.lower().replace(' ', '-')}-itinerary.json", "application/json")
else:
    st.markdown("### Start with a destination")
    st.write("Choose the shape of your trip in the sidebar. The planner works immediately without accounts, API keys, or model downloads.")
