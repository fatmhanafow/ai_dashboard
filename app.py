# app.py
import feedparser
import streamlit as st
from transformers import pipeline
import time

st.set_page_config(page_title="AI News Dashboard", page_icon="🤖", layout="wide")
st.title("🤖 AI News Dashboard — Local Summarizer")
st.markdown("نمایش آخرین اخبار از منابع منتخب با خلاصه‌ی لوکال و های‌لایت ۳ خبر مهم")

SOURCES = {
    "The Decoder": "https://the-decoder.com/feed/",
    "r/LocalLLaMA": "https://www.reddit.com/r/LocalLLaMA/.rss",
    "r/OpenAI": "https://www.reddit.com/r/OpenAI/.rss"
}

@st.cache_resource
def get_summarizer():
    try:
        # مدل سبک و مناسب برای summarization
        return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    except Exception as e:
        st.warning("⚠️ بارگذاری مدل خلاصه‌ساز به مشکل خورد. از خلاصه‌ی ساده استفاده خواهد شد.")
        return None

summarizer = get_summarizer()

def simple_summary(text, max_chars=220):
    # fallback ساده: چند جمله اول یا برش متن
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    sentences = text.split(". ")
    if len(sentences) >= 2:
        s = ". ".join(sentences[:2]).strip()
        if not s.endswith("."):
            s += "."
        return s[:max_chars]
    return text[:max_chars]

def summarize_text(text):
    if not text:
        return ""
    if summarizer:
        try:
            out = summarizer(text, max_length=60, min_length=20, do_sample=False)
            return out[0]["summary_text"].strip()
        except Exception:
            return simple_summary(text)
    else:
        return simple_summary(text)

# UI controls
with st.sidebar:
    st.header("تنظیمات")
    top_n = st.number_input("تعداد خبرهای مهم برای های‌لایت", min_value=1, max_value=10, value=3)
    per_source = st.number_input("تعداد خبر از هر منبع", min_value=1, max_value=10, value=3)
    if st.button("رفرش (بازخوانی)"):
        st.experimental_rerun()

all_news = []
now = time.strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"آخرین بروزرسانی: {now}")

# جمع‌آوری و خلاصه‌سازی
for src_name, url in SOURCES.items():
    try:
        feed = feedparser.parse(url)
    except Exception:
        feed = None

    if not feed or not getattr(feed, "entries", None):
        # هیچ ورودی — رد کن
        continue

    for entry in feed.entries[:per_source]:
        title = entry.get("title", "")
        link = entry.get("link", "")
        raw = entry.get("summary", entry.get("description", title))
        summary = summarize_text(raw)
        # امتیاز ساده: طول خلاصه + وزن کلمات مهم
        score = len(summary)
        keywords = ["OpenAI", "Anthropic", "Microsoft", "AI", "LLM", "model"]
        text_lower = (title + " " + raw).lower()
        for kw in keywords:
            if kw.lower() in text_lower:
                score += 25
        all_news.append({
            "source": src_name,
            "title": title,
            "link": link,
            "summary": summary,
            "score": score
        })

if not all_news:
    st.info("هیچ خبری پیدا نشد. منابع یا اتصال اینترنت را بررسی کنید.")
else:
    # های‌لایت
    top_news = sorted(all_news, key=lambda x: x["score"], reverse=True)[:top_n]

    st.header("🔥 ۳ خبر مهم (های‌لایت)")
    for n, news in enumerate(top_news, start=1):
        st.subheader(f"{n}. {news['title']}")
        st.markdown(f"*منبع: {news['source']}*")
        st.write(news['summary'])
        st.markdown(f"[لینک خبر]({news['link']})")
        st.markdown("---")

    st.header("📰 بقیه اخبار")
    for news in all_news:
        if news in top_news: 
            continue
        st.subheader(news["title"])
        st.markdown(f"*منبع: {news['source']}*")
        st.write(news["summary"])
        st.markdown(f"[لینک خبر]({news['link']})")
        st.markdown("---")
