import json
import requests
import streamlit as st

st.set_page_config(page_title="VIPEX Coach", layout="wide")

API_BASE = st.sidebar.text_input(
    "API Base URL",
    value="https://vipex-coach-api-2315.azurewebsites.net"
).rstrip("/")

st.title("VIPEX Coach")
st.caption("Azure-deployed agentic AI workflow for idea processing, worker execution, feedback, and ops monitoring.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Submit Ideas",
    "Jobs",
    "Ops Health",
    "Feedback",
    "Rules"
])

with tab1:
    st.subheader("Submit Teams-style Ideas")

    conversation_id = st.text_input("Conversation ID", value="demo-conv-001")
    user_id = st.text_input("User ID", value="naman")
    market = st.text_input("Market", value="VN")
    brand = st.text_input("Brand", value="TestBrand")
    workshop = st.text_input("Workshop", value="pilot")
    language = st.text_input("Language", value="en")

    ideas_text = st.text_area(
        "Raw Ideas",
        value="Create a loyalty campaign for high-value customers\nOffer service reminders based on vehicle age",
        height=150
    )

    if st.button("Submit Ideas"):
        payload = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "market": market,
            "brand": brand,
            "workshop": workshop,
            "language": language,
            "raw_ideas": [x.strip() for x in ideas_text.splitlines() if x.strip()]
        }

        res = requests.post(f"{API_BASE}/teams/message", json=payload, timeout=120)
        st.write("Status:", res.status_code)
        try:
            st.json(res.json())
        except Exception:
            st.text(res.text)

with tab2:
    st.subheader("Recent Jobs")

    if st.button("Refresh Jobs"):
        res = requests.get(f"{API_BASE}/jobs", timeout=60)
        st.write("Status:", res.status_code)
        jobs = res.json()
        st.json(jobs)

        if isinstance(jobs, list):
            for job in jobs:
                with st.expander(f"{job.get('job_id')} — {job.get('status')}"):
                    st.write("Conversation:", job.get("conversation_id"))
                    st.write("Attempts:", job.get("attempts"))
                    st.write("Error:", job.get("error"))

                    result_json = job.get("result_json")
                    if result_json:
                        try:
                            result = json.loads(result_json)
                            st.json(result)
                        except Exception:
                            st.text(result_json)

with tab3:
    st.subheader("Ops / Queue Health")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Queue Status"):
            res = requests.get(f"{API_BASE}/ops/queue", timeout=60)
            st.write("Status:", res.status_code)
            st.json(res.json())

    with col2:
        if st.button("Release Gates"):
            res = requests.get(f"{API_BASE}/ops/release-gates", timeout=60)
            st.write("Status:", res.status_code)
            st.json(res.json())

    with col3:
        if st.button("Drift Check"):
            res = requests.get(f"{API_BASE}/ops/drift", timeout=60)
            st.write("Status:", res.status_code)
            st.json(res.json())

    st.divider()

    if st.button("Process One Worker Message"):
        res = requests.post(f"{API_BASE}/worker/process-one", timeout=120)
        st.write("Status:", res.status_code)
        st.json(res.json())

    if st.button("Drain Worker Queue"):
        res = requests.post(f"{API_BASE}/worker/drain?max_messages=5", timeout=120)
        st.write("Status:", res.status_code)
        st.json(res.json())

with tab4:
    st.subheader("Feedback Stats")

    if st.button("Load Feedback Stats"):
        res = requests.get(f"{API_BASE}/feedback/stats", timeout=60)
        st.write("Status:", res.status_code)
        st.json(res.json())

    st.divider()
    st.subheader("Submit Feedback")

    idea_id = st.text_input("Idea ID", value="idea_demo")
    fb_conversation_id = st.text_input("Feedback Conversation ID", value="demo-conv-001")
    fb_market = st.text_input("Feedback Market", value="VN")
    signal = st.selectbox("Signal", ["accept", "reject", "edit", "needs_sme_review"])
    reason = st.text_area("Reason", value="Demo feedback from UI")

    if st.button("Submit Feedback"):
        payload = {
            "idea_id": idea_id,
            "conversation_id": fb_conversation_id,
            "market": fb_market,
            "signal": signal,
            "reason": reason
        }

        res = requests.post(f"{API_BASE}/feedback", json=payload, timeout=60)
        st.write("Status:", res.status_code)
        st.json(res.json())

with tab5:
    st.subheader("Capture Market Rule")

    rule_market = st.text_input("Rule Market", value="VN")
    category = st.text_input("Category", value="pricing")
    constraint = st.text_area(
        "Constraint",
        value="Do not recommend ideas requiring more than 10% discount without SME review"
    )
    rationale = st.text_area("Rationale", value="Protect margin and avoid invalid promotions")
    captured_by = st.text_input("Captured By", value="naman")
    source_conversation_id = st.text_input("Source Conversation ID", value="demo-conv-001")
    valid_from = st.text_input("Valid From", value="2026-06-11")
    hardness = st.selectbox("Hardness", ["hard_constraint", "soft_resistance", "unknown"])

    if st.button("Capture Rule"):
        payload = {
            "market": rule_market,
            "category": category,
            "constraint": constraint,
            "rationale": rationale,
            "captured_by": captured_by,
            "source_conversation_id": source_conversation_id,
            "valid_from": valid_from,
            "hardness": hardness
        }

        res = requests.post(f"{API_BASE}/rules", json=payload, timeout=60)
        st.write("Status:", res.status_code)
        st.json(res.json())