import streamlit as st
from groq import Groq
import base64
import json
from PIL import Image
import io

# Page config 
st.set_page_config(
    page_title="Saathi — साथी",
    page_icon="🤝",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] { font-family: 'Sora', sans-serif; }

  .main { background-color: #0d1117; }

  .saathi-header {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
  }

  .saathi-title {
    font-size: 2.8rem;
    font-weight: 700;
    color: #ff9933;
    margin: 0;
    letter-spacing: -0.02em;
  }

  .saathi-nepali {
    font-size: 1.1rem;
    color: #7a8899;
    margin: 0;
  }

  .saathi-tagline {
    font-size: 0.9rem;
    color: #7a8899;
    margin-top: 0.4rem;
  }

  .result-box {
    background: #161b22;
    border: 1px solid #2a3441;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin: 0.75rem 0;
  }

  .result-label {
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #ff9933;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }

  .urgent-banner {
    background: rgba(248,81,73,0.1);
    border: 1px solid rgba(248,81,73,0.3);
    border-radius: 8px;
    padding: 0.6rem 0.9rem;
    font-size: 0.85rem;
    color: #f85149;
    margin-bottom: 0.75rem;
  }

  .step-item {
    padding: 0.35rem 0;
    font-size: 0.9rem;
    color: #e8edf3;
  }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="saathi-header">
  <p class="saathi-title">🤝 Saathi</p>
  <p class="saathi-nepali">साथी — companion</p>
  <p class="saathi-tagline">Bilingual AI assistant for understanding American documents</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# Groq client 
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Language toggle 
lang = st.radio(
    "Response language",
    ["English + नेपाली", "English only", "नेपाली मात्र"],
    horizontal=True,
    index=0
)

# ── Quick templates ────────────────────────────────────────────────────────────
TEMPLATES = {
    "🏥 Medicaid": 'I received a letter from Medicaid saying: "Your Medicaid benefits may be terminated effective 30 days from this notice due to failure to provide verification documents. You have the right to appeal."',
    "🏠 Lease": 'My landlord says: "Tenant may not sublet without written consent. Failure to pay rent within 5 days results in a $75/day late fee."',
    "🏫 School": 'The school sent: "Complete this Proof of Residency form within 10 business days. Required: utility bill, photo ID, immunization records."',
    "💡 Utility": 'Electric company: "FINAL NOTICE: Your balance of $347.50 is 60 days past due. Service disconnection scheduled in 10 days."',
    "⚠️ Eviction": 'I got a paper: "THREE DAY NOTICE TO PAY OR QUIT. Pay $1,200 rent within 3 days or vacate. Legal proceedings will follow."',
}

st.markdown("**Quick templates — click to load:**")
cols = st.columns(len(TEMPLATES))
selected_template = ""
for i, (label, text) in enumerate(TEMPLATES.items()):
    if cols[i].button(label, use_container_width=True):
        selected_template = text

# Input area 
st.markdown("#### Paste document text or describe what you received:")
doc_text = st.text_area(
    "",
    value=selected_template,
    placeholder="Example: 'I got a letter from Medicaid saying my benefits may stop. What does this mean?'",
    height=140,
    label_visibility="collapsed"
)

st.markdown("#### Or upload a photo of the document:")
uploaded_file = st.file_uploader(
    "",
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="collapsed",
    help="Take a photo of any letter, form, or document"
)

# Show image preview if uploaded
image_b64 = None
if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="📷 Document photo attached", use_column_width=True)

    # Convert to base64 for the API
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

# Analyze button 
analyze = st.button("✦ Explain this →", type="primary", use_container_width=True)

if analyze:
    if not doc_text.strip() and not image_b64:
        st.warning("Please paste some text or upload a photo first.")
    else:
        # Build language instruction
        if "English only" in lang:
            lang_instruction = "Respond ONLY in English. Set nepali to empty string."
        elif "मात्र" in lang:
            lang_instruction = "Respond ONLY in Nepali (Devanagari script). Set english to empty string."
        else:
            lang_instruction = "Respond in BOTH English and Nepali."

        system_prompt = f"""You are Saathi, a bilingual AI assistant helping Bhutanese-American community members understand American documents. Many users speak Nepali and are unfamiliar with US bureaucratic systems.

Your job:
1. Explain what the document means in simple, warm language
2. Tell them exactly what action they need to take
3. Flag anything urgent or time-sensitive
4. Be reassuring — many users are anxious about official mail

{lang_instruction}

Respond ONLY with valid JSON (no markdown, no backticks):
{{
  "english": "Clear English explanation in 3-5 sentences.",
  "nepali": "नेपालीमा व्याख्या (३-५ वाक्य)",
  "nextSteps": ["Step 1", "Step 2", "Step 3"],
  "urgency": "low|medium|high",
  "documentType": "Brief label"
}}"""

        with st.spinner("Saathi is reading your document..."):
            try:
                # Build message — image or text
                if image_b64:
                    
                    user_content = [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": f"Please read and explain this document image.{' Additional context: ' + doc_text if doc_text.strip() else ''}"
                        }
                    ]
                    model = "meta-llama/llama-4-scout-17b-16e-instruct"
                else:
                    user_content = f"Please explain this document:\n\n{doc_text}"
                    model = "llama-3.3-70b-versatile"

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )

                raw = response.choices[0].message.content
                clean = raw.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean)

                # Display results 

                # Urgency banner
                if parsed.get("urgency") == "high":
                    st.markdown('<div class="urgent-banner">⚠️ <strong>Time-sensitive:</strong> This document requires action soon.</div>', unsafe_allow_html=True)

                # English explanation
                if parsed.get("english") and "मात्र" not in lang:
                    st.markdown('<div class="result-box"><div class="result-label">🇺🇸 English Explanation</div>' + parsed["english"] + '</div>', unsafe_allow_html=True)

                # Nepali explanation
                if parsed.get("nepali") and "English only" not in lang:
                    st.markdown('<div class="result-box"><div class="result-label">🇳🇵 नेपाली व्याख्या</div>' + parsed["nepali"] + '</div>', unsafe_allow_html=True)

                # Next steps
                if parsed.get("nextSteps"):
                    st.markdown("**📌 What to do next:**")
                    for i, step in enumerate(parsed["nextSteps"], 1):
                        st.markdown(f"{i}. {step}")

            except json.JSONDecodeError:
                st.error("Could not parse the response. Please try again.")
            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

# Footer 
st.divider()
st.markdown(
    "<p style='text-align:center; color:#7a8899; font-size:0.8rem;'>Built for the <strong style='color:#ff9933'>Bhutanese-American community</strong> · Saathi means 'companion' in Nepali</p>",
    unsafe_allow_html=True
)
