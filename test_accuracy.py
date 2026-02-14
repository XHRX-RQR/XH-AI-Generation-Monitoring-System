"""
AI Content Detector - Accuracy Test Suite

Tests with known human-written and AI-generated samples.
"""

import json
import sys
import time
from detector import AIDetector, DetectionError

API_BASE = "https://arenac-2api.rand0mk4cas.workers.dev/v1"
API_KEY = "sk-dummy-67ujhgfrtyujhgfdert6yujhgfrtyhn"
MODEL = "gpt-5.2"

# ── Test Samples ──
# Each sample: (text, expected_label, source_description)

SAMPLES = [
    # ─── Human-written samples ───
    (
        """I still remember the mass of September mornings when my dad drove me to school in his rusted-out Camry. The heater barely worked, so we'd sit there shivering, windows fogging up while he told bad jokes about why the chicken crossed the road. I never laughed, but god, I miss those mornings now. College is fine, I guess? The food sucks, my roommate snores like a chainsaw, and I've already lost two umbrellas. But there's this coffee shop on 4th street that plays old jazz records and the barista always draws a little cat in my latte foam. Small things, you know?""",
        "Human-written",
        "Personal blog post / memoir style"
    ),
    (
        """ok so basically what happened was my cat knocked over my monitor at like 3am and I wake up to this CRASH and glass everywhere and the cat is just sitting there looking at me like nothing happened?? I swear this animal has zero remorse. anyway now im coding on my laptop which is like 13 inches and my eyes are dying. does anyone know if the LG 27GP850 ever goes on sale because im broke af after paying rent this month lol""",
        "Human-written",
        "Casual Reddit/forum post"
    ),
    (
        """The patient presented with a 3-day history of progressive dyspnea and nonproductive cough. Physical examination revealed bilateral basal crackles and an SpO2 of 88% on room air. Chest X-ray showed diffuse bilateral infiltrates consistent with ARDS. We initiated prone positioning and low-tidal-volume ventilation per ARDSNet protocol. The family was understandably distraught — I spent about 40 minutes with them explaining the situation, which is never easy. Labs came back showing a ferritin of 1,847, which made me think we might be dealing with something more systemic here.""",
        "Human-written",
        "Medical case note with personal voice"
    ),
    (
        """昨天下班路上看到一个老大爷在路边摆摊卖自己种的橘子，五块钱一大袋，我买了两袋。回家一尝，酸得我眼泪都出来了，但是那种酸里面有股特别的甜，就是小时候在外婆家后院摘的那种味道。现在超市里的水果都长得漂漂亮亮的，但总觉得少了点什么。也许是少了泥土的味道吧。""",
        "Human-written",
        "Chinese personal essay"
    ),
    (
        """Look, I've been in this industry for 22 years and I'm telling you — microservices are not the answer to everything. We ripped apart a perfectly good monolith last year because some architect fresh out of a conference convinced leadership it was "the modern way." Result? 47 services, a Kubernetes cluster that costs us $18K/month, and deployments that take 3x longer. Sometimes a well-structured monolith is EXACTLY what you need. Fight me on this.""",
        "Human-written",
        "Opinionated tech blog / rant"
    ),

    # ─── AI-generated samples ───
    (
        """Artificial intelligence has transformed numerous industries in recent years, fundamentally reshaping how businesses operate and deliver value to their customers. From healthcare to finance, the applications of AI are vast and continue to expand at an unprecedented pace. Machine learning algorithms, in particular, have demonstrated remarkable capabilities in pattern recognition, natural language processing, and predictive analytics. As organizations increasingly adopt these technologies, it becomes essential to consider both the opportunities and challenges they present. Ethical considerations, data privacy concerns, and the need for transparent decision-making processes are all critical factors that must be addressed as we navigate this transformative era of technological advancement.""",
        "AI-generated",
        "Generic AI essay on AI"
    ),
    (
        """Effective time management is a crucial skill that can significantly impact both personal and professional success. By implementing strategic approaches to organizing tasks and priorities, individuals can maximize their productivity and achieve their goals more efficiently. One of the most important strategies is the Eisenhower Matrix, which categorizes tasks based on urgency and importance. Additionally, techniques such as time blocking, the Pomodoro method, and the two-minute rule can help individuals maintain focus and reduce procrastination. It's important to note that finding the right combination of strategies requires experimentation and self-awareness. Furthermore, regular reflection on one's time management practices can lead to continuous improvement and better work-life balance.""",
        "AI-generated",
        "Generic AI advice article"
    ),
    (
        """The Renaissance period, spanning roughly from the 14th to the 17th century, represents one of the most significant cultural and intellectual transformations in European history. This era was characterized by a renewed interest in classical Greek and Roman art, literature, and philosophy. Key figures such as Leonardo da Vinci, Michelangelo, and Raphael produced masterpieces that continue to inspire artists today. The movement began in Italy, particularly in Florence, before spreading throughout Europe. The Renaissance also saw significant advancements in science, with figures like Galileo Galilei and Nicolaus Copernicus challenging established views of the universe. Moreover, the invention of the printing press by Johannes Gutenberg revolutionized the dissemination of knowledge, making books more accessible to a broader audience.""",
        "AI-generated",
        "AI-generated history summary"
    ),
    (
        """Climate change represents one of the most pressing challenges facing humanity in the 21st century. The scientific consensus is clear: human activities, particularly the burning of fossil fuels and deforestation, are driving unprecedented changes in Earth's climate system. Rising global temperatures have led to more frequent and severe weather events, including hurricanes, droughts, and wildfires. The melting of polar ice caps and glaciers is contributing to rising sea levels, threatening coastal communities worldwide. To address this crisis, a multifaceted approach is needed that combines technological innovation, policy reform, and individual action. Renewable energy sources such as solar, wind, and hydroelectric power offer promising alternatives to fossil fuels. Additionally, international cooperation through frameworks like the Paris Agreement is essential for coordinating global efforts to reduce greenhouse gas emissions.""",
        "AI-generated",
        "AI-generated climate change essay"
    ),
    (
        """Python is a versatile and powerful programming language that has gained immense popularity among developers worldwide. Its clean syntax and readability make it an excellent choice for beginners, while its extensive library ecosystem provides advanced capabilities for experienced programmers. Python excels in various domains, including web development, data science, machine learning, and automation. Frameworks such as Django and Flask simplify web application development, while libraries like NumPy, Pandas, and Scikit-learn provide robust tools for data analysis and machine learning. Furthermore, Python's strong community support ensures that developers have access to comprehensive documentation, tutorials, and third-party packages. Whether you're building a simple script or a complex application, Python offers the flexibility and tools needed to bring your ideas to life.""",
        "AI-generated",
        "AI-generated Python overview"
    ),
]


def run_tests():
    print("=" * 60)
    print("  AI Content Detector - Accuracy Test Suite")
    print("=" * 60)
    print(f"  API: {API_BASE}")
    print(f"  Model: {MODEL}")
    print(f"  Samples: {len(SAMPLES)}")
    print("=" * 60)

    detector = AIDetector(
        api_base=API_BASE,
        api_key=API_KEY,
        model=MODEL,
        temperature=0.1,
        timeout=180,
    )

    results = []
    correct = 0
    total = len(SAMPLES)

    for i, (text, expected, desc) in enumerate(SAMPLES):
        print(f"\n[{i+1}/{total}] Testing: {desc}")
        print(f"  Expected: {expected}")

        try:
            result = detector.detect(text)
            verdict = result.get("verdict", "Inconclusive")
            confidence = result.get("confidence", 0)
            ai_prob = result.get("ai_probability", 0)

            # Determine if correct
            is_correct = False
            if "ai" in expected.lower() and "ai" in verdict.lower():
                is_correct = True
            elif "human" in expected.lower() and "human" in verdict.lower():
                is_correct = True

            if is_correct:
                correct += 1
                status = "PASS"
            else:
                status = "FAIL"

            print(f"  Verdict:  {verdict} (confidence: {confidence}%, AI prob: {ai_prob}%)")
            print(f"  Result:   [{status}]")

            results.append({
                "desc": desc,
                "expected": expected,
                "verdict": verdict,
                "confidence": confidence,
                "ai_probability": ai_prob,
                "correct": is_correct,
                "elapsed": result.get("elapsed_seconds", 0),
            })

        except DetectionError as e:
            print(f"  ERROR: {e}")
            results.append({
                "desc": desc,
                "expected": expected,
                "verdict": "ERROR",
                "confidence": 0,
                "ai_probability": 0,
                "correct": False,
                "error": str(e),
            })

        # Small delay between requests
        time.sleep(1)

    # Summary
    accuracy = (correct / total) * 100 if total > 0 else 0
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    print(f"  Total samples: {total}")
    print(f"  Correct:       {correct}")
    print(f"  Accuracy:      {accuracy:.1f}%")
    print("=" * 60)

    # Detailed breakdown
    human_samples = [r for r in results if "human" in r["expected"].lower()]
    ai_samples = [r for r in results if "ai" in r["expected"].lower()]
    human_correct = sum(1 for r in human_samples if r["correct"])
    ai_correct = sum(1 for r in ai_samples if r["correct"])

    print(f"\n  Human-written: {human_correct}/{len(human_samples)} correct")
    print(f"  AI-generated:  {ai_correct}/{len(ai_samples)} correct")

    if accuracy >= 90:
        print(f"\n  [PASS] Accuracy target met (>= 90%)")
    else:
        print(f"\n  [FAIL] Accuracy below target (< 90%)")

    print("=" * 60)

    # Save results
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump({"accuracy": accuracy, "correct": correct, "total": total, "results": results}, f, indent=2, ensure_ascii=False)
    print("  Results saved to test_results.json")

    return accuracy


if __name__ == "__main__":
    acc = run_tests()
    sys.exit(0 if acc >= 90 else 1)
