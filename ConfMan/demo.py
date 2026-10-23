"""Rich demo data: 3 conferences, 30 papers, admin, chairs, reviewers, payments.

History is generated with a simulated clock so charts, activity and 'x days ago' look real.
All demo accounts use the password Demo@1234 (local demos only).
"""
import os
import textwrap
import uuid
from datetime import date, datetime, timedelta

from cms_app import db as dbm, services as svc

PASSWORD = "Demo@1234"

CHAIRS = [("chair@demo.org", "Dr. Priya Raman", "LICET, Chennai"),
          ("chair2@demo.org", "Dr. Karthik Subramanian", "IISc Bengaluru"),
          ("chair3@demo.org", "Prof. Meenakshi Iyer", "PSG Tech, Coimbatore")]
REVIEWERS = [
    ("reviewer1@demo.org", "Dr. Ravi Kumar", "Anna University", "software engineering, testing, requirements, agile, code review, technical debt"),
    ("reviewer2@demo.org", "Dr. Meena Lakshmi", "IIT Madras", "machine learning, deep learning, nlp, forecasting, data analytics, reinforcement learning"),
    ("reviewer3@demo.org", "Prof. Kiran Das", "NIT Trichy", "computer networks, iot, wireless, routing, sdn, 5g, edge"),
    ("reviewer4@demo.org", "Dr. Latha Narayanan", "Infosys Research", "cloud computing, microservices, devops, kubernetes, serverless, architecture"),
    ("reviewer5@demo.org", "Dr. Sanjay Mehta", "IIIT Hyderabad", "cybersecurity, cryptography, blockchain, privacy, phishing, security"),
    ("reviewer6@demo.org", "Dr. Divya Prakash", "TCS Research", "data analytics, visualization, databases, big data, streaming, data quality"),
]
AUTHORS = [("author@demo.org", "Asha Krishnan", "LICET, Chennai"), ("author2@demo.org", "Rohit Menon", "VIT Vellore"),
           ("author3@demo.org", "Sneha Reddy", "SRM University"), ("author4@demo.org", "Arjun Nair", "Amrita University"),
           ("author5@demo.org", "Fatima Sheikh", "BITS Pilani"), ("author6@demo.org", "Vikram Joshi", "SASTRA University"),
           ("author7@demo.org", "Pooja Venkat", "Anna University"), ("author8@demo.org", "Imran Ali", "Manipal Institute"),
           ("author9@demo.org", "Divya Shankar", "Thiagarajar College"), ("author10@demo.org", "Karan Malhotra", "IIT Bombay")]
ATTENDEES = [("attendee@demo.org", "Anil Kumar", "Industry"), ("attendee2@demo.org", "Lakshmi Priya", "LICET, Chennai"),
             ("attendee3@demo.org", "Rahul Verma", "Wipro"), ("attendee4@demo.org", "Nisha Thomas", "Loyola College")]

# (title, keywords, track, conference, author index, abstract)
PAPERS = [
 ("Automated Test Case Generation for REST APIs Using Large Language Models", "llm, testing, rest api, automation", "Software Testing", 0, 0,
  "We prompt a large language model with OpenAPI specifications to generate executable test suites, and compare coverage and fault detection against schema-based fuzzers on twelve open-source services."),
 ("A Requirements Traceability Framework for Agile Teams", "requirements, agile, traceability", "Software Engineering", 0, 1,
  "Agile teams rarely keep requirements linked to code. We present a lightweight framework that links user stories, commits and tests automatically, and evaluate it with four student teams over one semester."),
 ("Predicting Software Defects with Graph Neural Networks", "defect prediction, machine learning, graph neural networks", "AI and Machine Learning", 0, 2,
  "We model code as a graph of calls and data flow and train a graph neural network to flag defect-prone modules, improving recall over metric-based baselines on five public datasets."),
 ("Flaky Test Detection in Continuous Integration Pipelines", "flaky tests, ci, testing, devops", "Software Testing", 0, 3,
  "Flaky tests waste developer time. This paper proposes a rerun-free detector that learns from build history and test timing, and reports a forty percent reduction in wasted CI minutes."),
 ("Explainable Code Review Suggestions with Transformers", "code review, nlp, deep learning", "AI and Machine Learning", 0, 4,
  "A transformer model suggests review comments and highlights the changed lines that triggered each suggestion, helping reviewers understand and trust the output."),
 ("Technical Debt Prioritisation Using Developer Telemetry", "technical debt, software metrics, maintenance", "Software Engineering", 0, 5,
  "We combine static-analysis findings with editor telemetry to rank technical debt by how often developers touch it, and validate the ranking with maintainers of three projects."),
 ("Mutation Testing at Scale: A Cost-Reduction Study", "mutation testing, testing, performance", "Software Testing", 0, 6,
  "Mutation testing is expensive. We evaluate selective mutation and test prioritisation on large Java codebases and show that most of the benefit is kept at a fraction of the cost."),
 ("Microservice Decomposition Guided by Domain-Driven Design", "microservices, architecture, ddd", "Software Engineering", 0, 7,
  "Starting from a monolithic e-commerce system, we derive service boundaries from bounded contexts and compare the result with clustering-based decomposition tools."),
 ("Reinforcement Learning for Adaptive Software Project Scheduling", "reinforcement learning, scheduling, project management", "AI and Machine Learning", 0, 0,
  "A reinforcement learning agent re-plans sprint schedules as estimates change. Simulations on historical project data show shorter delivery time than a fixed plan."),
 ("Effort Estimation with Function Points and Gradient Boosting", "effort estimation, function points, machine learning", "Software Engineering", 0, 8,
  "We combine unadjusted function points with project attributes in a gradient boosting model and reduce mean magnitude of relative error compared with COCOMO II on a public benchmark."),
 ("A Usability Evaluation Framework for Conference Management Systems", "usability, ux, evaluation", "Software Engineering", 0, 0,
  "We define task-based heuristics for conference systems and apply them to three platforms, finding that reviewer assignment and payment flows cause most user errors."),
 ("Naive Keyword Matching for Reviewer Assignment: Why It Fails", "reviewer assignment, nlp, peer review", "AI and Machine Learning", 0, 9,
  "A short study of keyword-overlap reviewer assignment on two small conferences, showing mismatched assignments in a third of cases."),
 ("Cost-Aware Autoscaling of Containerised Workloads on Kubernetes", "cloud, kubernetes, autoscaling, devops", "Cloud Computing", 1, 1,
  "We extend the Kubernetes horizontal pod autoscaler with a cost signal and show up to 28 percent lower cloud spend with the same latency targets on bursty web workloads."),
 ("Serverless Cold-Start Mitigation Using Predictive Warm Pools", "serverless, cloud, latency", "Cloud Computing", 1, 2,
  "A forecasting model keeps a small pool of warm function instances based on request history, cutting tail latency of cold starts on three serverless platforms."),
 ("Real-Time Dashboards over Streaming Sales Data with Apache Kafka", "streaming, kafka, data analytics, visualization", "Data Analytics", 1, 3,
  "We design a streaming pipeline that feeds live sales dashboards for a retail chain and discuss windowing, late data and the cost of exactly-once delivery."),
 ("Data Quality Checks for Machine Learning Feature Stores", "data quality, feature store, big data", "Big Data Engineering", 1, 4,
  "A declarative set of data quality checks runs inside the feature store pipeline and blocks bad batches before training, catching schema drift and null spikes early."),
 ("Federated Analytics for Hospital Occupancy Forecasting", "federated learning, forecasting, privacy", "Data Analytics", 1, 5,
  "Hospitals train a shared occupancy forecasting model without exchanging patient records. We report accuracy close to centralised training on regional admission data."),
 ("Comparing Columnar Formats for Analytical Queries on S3", "parquet, s3, databases, big data", "Big Data Engineering", 1, 6,
  "Parquet and ORC are compared across file sizes, compression and query engines on S3, with practical guidance for choosing partitioning schemes."),
 ("Infrastructure as Code Drift Detection in Multi-Cloud Setups", "terraform, iac, cloud, devops", "Cloud Computing", 1, 7,
  "We detect and classify configuration drift between Terraform state and live resources on two cloud providers, and measure the time operators need to reconcile it."),
 ("Customer Churn Prediction Using Explainable Gradient Boosting", "churn, machine learning, analytics", "Data Analytics", 1, 8,
  "A gradient boosting churn model with SHAP explanations is tested on telecom data; the explanations help retention teams choose offers."),
 ("Scalable Log Analytics with OpenSearch for Small Teams", "logging, opensearch, observability", "Big Data Engineering", 1, 9,
  "A low-cost OpenSearch deployment pattern for teams with limited operations staff, with retention, index lifecycle and alerting recommendations."),
 ("A Cost Model for Hybrid Cloud Data Warehouses", "cloud, data warehouse, cost", "Cloud Computing", 1, 0,
  "We build a simple cost model that compares on-premise, cloud and hybrid data warehouse deployments for mid-sized organisations."),
 ("Energy-Efficient Routing in LoRaWAN Sensor Networks", "lora, routing, iot, energy", "Internet of Things", 2, 0,
  "A duty-cycle aware routing scheme extends the battery life of LoRaWAN sensor nodes by 35 percent in a campus deployment of 120 nodes."),
 ("Detecting DDoS Traffic with Lightweight Machine Learning at the Edge", "ddos, edge, machine learning, security", "Cybersecurity", 2, 1,
  "A compact classifier runs on edge gateways and detects volumetric DDoS traffic with high accuracy while using very little memory."),
 ("Software-Defined Networking for Campus Wi-Fi Load Balancing", "sdn, wifi, networks", "Computer Networks", 2, 2,
  "An SDN controller steers clients between access points based on load and signal quality, improving throughput in lecture halls during peak hours."),
 ("Secure Over-the-Air Updates for Constrained IoT Devices", "ota, security, iot, cryptography", "Cybersecurity", 2, 3,
  "A signed, resumable update protocol for microcontrollers with under 64 KB of RAM, evaluated for security and update time on three boards."),
 ("Smart Irrigation Using Soil Sensors and Weather Forecasts", "iot, agriculture, sensors", "Internet of Things", 2, 4,
  "Soil moisture sensors and rainfall forecasts drive an irrigation controller that saved 22 percent of water in a six-week farm trial."),
 ("5G Network Slicing for Low-Latency Industrial Control", "5g, network slicing, latency", "Computer Networks", 2, 5,
  "We evaluate network slicing for factory control loops in a 5G testbed and report latency and jitter under mixed traffic."),
 ("Phishing URL Detection Using Character-Level CNNs", "phishing, deep learning, security", "Cybersecurity", 2, 6,
  "A character-level convolutional network classifies phishing URLs without hand-crafted features, but we only test on a single dataset."),
 ("Blockchain-Based Certificate Verification for Universities", "blockchain, certificates, security", "Cybersecurity", 2, 7,
  "Degree certificates are anchored on a permissioned blockchain so employers can verify them instantly; we describe the design and a pilot with two colleges."),
]

# paper number (1-based) -> (days ago submitted, [(reviewer idx 1-6, score or None)])
PLAN = {
 1: (1, []), 2: (2, []), 3: (7, [(2, None)]), 4: (3, []), 5: (11, [(2, None)]),
 6: (16, [(1, None)]), 7: (19, [(1, None)]), 8: (20, [(1, None), (4, 8)]),
 9: (23, [(2, 7), (6, None), (4, None)]), 10: (30, [(1, 8), (2, 9)]),
 11: (34, [(1, 8), (2, 9), (6, 8)]), 12: (31, [(2, 3), (1, 4)]),
 13: (2, []), 14: (6, [(3, None)]), 15: (5, []), 16: (8, []), 17: (9, []),
 18: (13, [(6, None)]), 19: (17, [(4, 7), (5, None)]), 20: (22, [(6, 6), (2, 7)]),
 21: (27, [(4, 6), (6, 6)]), 22: (12, [(4, None)]),
 23: (58, [(3, 9), (5, 8)]), 24: (56, [(3, 8), (5, 9)]), 25: (54, [(3, 8), (4, 7)]),
 26: (52, [(5, 9), (3, 8)]), 27: (50, [(3, 8), (5, 7)]), 28: (49, [(3, 6), (4, 6)]),
 29: (47, [(5, 3), (3, 4)]), 30: (45, [(5, 8), (3, 7)]),
}
DECIDE = {11: "Accepted", 12: "Rejected", 21: "Revision Required", 23: "Accepted", 24: "Accepted",
          25: "Accepted", 26: "Accepted", 27: "Accepted", 28: "Revision Required", 29: "Rejected"}
COMMENTS = {
    "high": ["Clear contribution and a well designed evaluation. The results are convincing and the writing is easy to follow. Please add more detail on threats to validity.",
             "Strong paper. The method is sound and the comparison with baselines is fair. A small ablation study would make it even better."],
    "mid": ["The idea is reasonable but the evaluation is thin. Please add more datasets and explain the experimental setup in more detail before publication.",
            "Interesting direction with a useful prototype. The related work section is incomplete and some claims are not supported by the data shown."],
    "low": ["The contribution is limited and the evaluation does not support the main claims. The approach is evaluated on a single small dataset.",
            "The problem is relevant, but the method is not novel enough and the paper lacks a proper comparison with existing work."],
}


def make_pdf(title, abstract):
    lines = [title, ""] + textwrap.wrap(abstract, 85) + ["", "Demo paper generated by ConfMan for exploring the system."]
    text = "BT /F1 14 Tf 60 780 Td 18 TL\n" + "\n".join(
        f"({ln.replace(chr(92), '').replace('(', '[').replace(')', ']')}) Tj T*" for ln in lines) + "\nET"
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            f"<< /Length {len(text)} >>\nstream\n{text}\nendstream", "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offsets = "%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF"
    return out.encode("latin-1", "replace")


def load_demo(app):
    db = dbm.get_db()
    now = datetime.now().replace(microsecond=0)
    clock = {"t": now}
    svc.set_clock(lambda: clock["t"])

    def at(dt):
        clock["t"] = min(dt, now - timedelta(minutes=20))

    def day(n, hour=10):
        return (now - timedelta(days=n)).replace(hour=hour, minute=(n * 7) % 60)

    try:
        _build(app, db, now, at, day)
    finally:
        svc.set_clock(None)
    db.commit()


def _build(app, db, now, at, day):
    today = now.date()
    at(day(75))
    admin = svc.register_user(db, "Anita Rao", "admin@demo.org", PASSWORD, "admin", "LICET, Chennai")
    chairs = [svc.register_user(db, n, e, PASSWORD, "chair", a) for e, n, a in CHAIRS]
    at(day(70))
    revs = {}
    for i, (e, n, a, x) in enumerate(REVIEWERS, 1):
        at(day(70 - i))
        revs[i] = svc.register_user(db, n, e, PASSWORD, "reviewer", a, x)
    authors = []
    for i, (e, n, a) in enumerate(AUTHORS):
        at(day(66 - i * 3))
        authors.append(svc.register_user(db, n, e, PASSWORD, "author", a))
    attendees = []
    for i, (e, n, a) in enumerate(ATTENDEES):
        at(day(40 - i * 8))
        attendees.append(svc.register_user(db, n, e, PASSWORD, "attendee", a))
    at(day(30))
    gone = svc.register_user(db, "Rahul Dropout", "inactive@demo.org", PASSWORD, "author", "Former user")
    at(day(9))
    svc.set_user_active(db, admin, gone, False)

    d = lambda n: (today + timedelta(days=n)).isoformat()
    confs = []
    specs = [
        (chairs[0], "International Conference on Software Engineering and AI 2026", "LICET, Chennai",
         "Software engineering practice meets machine learning: testing, requirements, architecture and AI-assisted development.",
         d(48), d(50), d(9), d(25), ["Software Engineering", "AI and Machine Learning", "Software Testing"], 62),
        (chairs[1], "National Symposium on Cloud, Data and Analytics 2026", "IISc, Bengaluru",
         "Cloud platforms, data engineering and analytics for industry and academia.",
         d(85), d(86), d(34), d(55), ["Cloud Computing", "Data Analytics", "Big Data Engineering"], 40),
        (chairs[2], "Smart Systems, IoT and Networks Summit 2026", "PSG Tech, Coimbatore",
         "Wireless networks, IoT deployments and network security, with industry demos.",
         d(20), d(21), d(-6), d(-10), ["Computer Networks", "Internet of Things", "Cybersecurity"], 75),
    ]
    for chair, name, venue, desc, s, e, sub, early, tracks, ago in specs:
        at(day(ago))
        cid = svc.create_conference(db, chair, name, venue, s, e, sub, early, desc)
        for t in tracks:
            svc.add_track(db, chair, cid, t)
        confs.append((cid, chair))
    track_id = {(c, r["name"]): r["track_id"] for c, _ in confs
                for r in db.execute("SELECT * FROM tracks WHERE conf_id=?", (c,))}
    uploads = app.config["UPLOAD_FOLDER"]
    os.makedirs(uploads, exist_ok=True)

    ids = {}
    for n, (title, kw, track, ci, ai, abstract) in enumerate(PAPERS, 1):
        ago, _ = PLAN[n]
        cid, chair = confs[ci]
        at(day(ago, 9 + n % 8))
        pid = svc.submit_paper(db, authors[ai], cid, track_id[(cid, track)], title, abstract, kw,
                               title.lower().replace(" ", "_")[:40] + ".pdf", today=(now - timedelta(days=ago)).date().isoformat())
        with open(os.path.join(uploads, f"{pid}_{uuid.uuid4().hex[:8]}.pdf"), "wb") as fh:
            fh.write(make_pdf(title, abstract))
        ids[n] = pid

    for n, (ago, plan) in PLAN.items():
        pid = ids[n]
        cid, chair = confs[PAPERS[n - 1][3]]
        when = day(ago) + timedelta(days=1, hours=2)
        for k, (ridx, score) in enumerate(plan):
            at(when + timedelta(hours=k * 3))
            asg = svc.assign_reviewer(db, chair, pid, revs[ridx])
            if score is not None:
                at(when + timedelta(days=2 + k, hours=5))
                band = "high" if score >= 7 else ("mid" if score >= 5 else "low")
                rec = {"high": "accept", "mid": "major revision", "low": "reject"}[band]
                if score == 7:
                    rec = "minor revision"
                svc.submit_review(db, revs[ridx], asg, score, COMMENTS[band][(n + k) % 2], rec)
        if n in DECIDE:
            at(when + timedelta(days=6, hours=4))
            remarks = {"Accepted": "Congratulations. Please prepare the camera-ready version.",
                       "Rejected": "Thank you for submitting. The reviewers found the contribution too limited for this edition.",
                       "Revision Required": "Please address the reviewers' comments and resubmit."}[DECIDE[n]]
            svc.record_decision(db, chair, pid, DECIDE[n], remarks)

    # sessions & programme for the summit (conference 3) and open sessions for the others
    c3, ch3 = confs[2]
    sd = d(20)
    at(day(60))
    sess = {
        "net": svc.create_session(db, ch3, c3, "Networks and SDN", "Hall A", f"{sd}T10:00", f"{sd}T11:30", 4),
        "iot": svc.create_session(db, ch3, c3, "IoT and Edge Systems", "Hall B", f"{sd}T10:00", f"{sd}T11:30", 3),
        "sec": svc.create_session(db, ch3, c3, "Security Session", "Hall A", f"{sd}T11:45", f"{sd}T13:00", 4),
    }
    c1, ch1 = confs[0]
    at(day(20))
    svc.create_session(db, ch1, c1, "Opening Keynote and Testing", "Hall A", f"{d(48)}T10:00", f"{d(48)}T11:30", 4)
    svc.create_session(db, ch1, c1, "AI for Software Engineering", "Hall B", f"{d(48)}T11:45", f"{d(48)}T13:00", 4)

    # registrations and payments
    def pay(user, cid, cat, card, ago):
        at(day(ago))
        rid = svc.register_for_conference(db, user, cid, cat, today=(now - timedelta(days=ago)).date().isoformat())
        if card:
            at(day(ago) + timedelta(minutes=14))
            try:
                svc.process_payment(db, user, rid, card)
            except svc.ServiceError:
                at(day(ago) + timedelta(minutes=20))
                svc.process_payment(db, user, rid, "4242424242424242")
        return rid
    for ai, n in [(0, 23), (1, 24), (2, 25), (3, 26)]:
        pay(authors[ai], c3, "student" if ai % 2 else "academic", "4242424242424242", 44 - ai)
    pay(authors[0], c1, "academic", None, 3)
    pay(attendees[0], c3, "industry", "4242424242424242", 30)
    pay(attendees[0], c1, "industry", None, 2)
    pay(attendees[1], c3, "student", "4242424242424242", 26)
    pay(attendees[1], c1, "student", "4242424242424242", 6)
    pay(attendees[2], c3, "industry", "4000000000000002", 21)   # declined once, then succeeds
    pay(attendees[3], c1, "student", "4242424242424242", 4)
    pay(attendees[3], c2 := confs[1][0], "student", None, 1)
    pay(authors[5], c2, "academic", "4242424242424242", 5)
    pay(authors[8], c1, "academic", "4242424242424242", 8)

    # schedule accepted papers of the summit
    at(day(12))
    for n, key in [(23, "iot"), (24, "sec"), (25, "net"), (26, "sec")]:
        svc.schedule_paper(db, ch3, ids[n], sess[key])

    # everything older than 3 days has been read
    db.execute("UPDATE notifications SET is_read=1 WHERE created_at < ?", ((now - timedelta(days=3)).isoformat(),))
    db.commit()
