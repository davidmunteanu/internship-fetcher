# About Me

David Munteanu. First-year Computer Science and Engineering student at TU Delft (2025–2028), Data Track. Current GPA: 8/10. Admitted through a selective entrance exam (math, logic, algorithmic thinking — ~10% acceptance rate). Based in Delft, Netherlands.

EU citizen (Romanian). Fully authorized to work in the Netherlands with no visa or sponsorship required.

Available for internships starting summer 2027 (June–August 2027, flexible on exact dates).

# Technical Skills

**Languages (daily use):** Python, JavaScript (Node.js, Express.js), Java (Spring Boot, JavaFX), SQL, HTML/CSS, Bash.

**Frameworks & tools:** Flask, Spring Boot, JavaFX, React (basic), Gunicorn, Maven, Google Guice, Mockito, TestFX.

**AI / ML:** Gemini API, Ollama, vLLM, faster-whisper (Whisper-based STT), pyannote (speaker diarization), piper (TTS), XGBoost, Random Forest, scikit-learn. Comfortable designing end-to-end AI pipelines — have built a fully local STT/TTS system and a model-vs-model evaluation framework.

**Data & APIs:** REST API design and consumption, OAuth 2.0 (Spotify API integration), SQLite (aiosqlite), H2, httpx (async HTTP with HTTP/2), web scraping via public JSON APIs (Greenhouse, Lever, SmartRecruiters).

**DevOps / Infra:** Git, GitLab CI/CD (pipeline optimization, artifact caching, branch protection), GitHub, Docker basics, Railway (deployment), ffmpeg (audio processing).

**Platforms:** UiPath suite — Orchestrator, Maestro, Studio, Data Fabric. Comfortable with RPA automation design, AI agent orchestration, and database-integrated dashboard development on the UiPath platform.

# Work Experience

## UiPath — Agentic Developer Intern (Jul–Oct 2026, Bucharest)

This is my most substantial professional experience. I delivered end-to-end implementations across 3 international client projects simultaneously, working directly with clients in different countries and industries.

**Project 1 — Aviation operations (Turkey):** Built a TypeScript/React dashboard integrated with a SQL database and UiPath Maestro for an airline operations client. Created targeted mock-ups for non-technical intermediaries to bridge the gap between dev-team and business stakeholders.

**Project 2 — Law enforcement (Romania):** Architected a fully local AI audio pipeline for a police agency, designed for department-wide deployment starting with the domestic-abuse phone line. The pipeline: ffmpeg audio normalization → pyannote speaker diarization → faster-whisper speech-to-text → piper text-to-speech, with a UI that syncs the transcript to the source audio. Designed to run entirely on-premise for data sensitivity reasons.

**Project 3 — Insurance (UK):** Built operational dashboards and led requirements gathering. Negotiated MVP scope directly with UK clients, ran client meetings solo when senior engineers were unavailable, and answered technical questions to company directors in English.

**Impact and recognition:**
- Performance on first project led the solution architect to assign me two additional projects.
- One project selected for presentation at a UiPath conference in Las Vegas; another potentially in London.
- Co-hosted the global interns meeting with the UiPath CEO.
- Invited back for a second internship by both my manager and the talent acquisition manager.

## The Human Quotient Lab @ TU Delft — Research Assistant (Mar 2026–present)

Researching adversarial LLM pen-testing: agentic attacker vs. defender chatbot setups, applying game theory and manipulation-topology techniques across stateful agents with varied topologies. Currently authoring a research paper.

Built a plug-and-play framework for model-vs-model evaluation using dual vLLM and Ollama backends, designed to test small language model variations in isolation.

## Step Up! — Founder & Project Manager (Jul 2024–Mar 2025, Bucharest)

Founded and managed a non-profit with 40+ participants and 0 budget that addressed the lack of career resources for high school students through workshops. Coordinated 7 volunteers and secured partnerships with IBM, Bosch, and others. Applied leadership frameworks from the Leaders Explore Program (top 30 selection in Bucharest).

# Projects

## Internship Tracker Bot — Python, httpx, aiosqlite, python-telegram-bot, Gemini API
Personal automation project. A bot that scrapes tech internship listings from company career pages via Greenhouse, Lever, and SmartRecruiters public JSON APIs, filters for relevant roles in the Netherlands, extracts application questions, generates draft answers using the Gemini API with my profile as context, and delivers everything to Telegram. Runs on Railway on a cron schedule with SQLite for deduplication.

## Spotyvibe — Flask, JavaScript, Python, Gemini API, Spotify API
Web app that maps Spotify listening history to emotional archetypes using Gemini API for analysis. Integrated Spotify API via OAuth 2.0, handled session persistence with Flask-Session, deployed a multi-threaded web server on Railway with Gunicorn.

## FoodPal (university project) — Java 24, Spring Boot, JavaFX, H2, GitLab CI/CD
Led a 6-person team building a multi-module recipe-sharing and nutrient-tracking platform. Refactored the architecture to a Singleton-patterned Controller structure using Google Guice, resolving circular dependencies. Optimized GitLab CI/CD pipelines by decoupling client/server builds and implementing artifact caching — reduced total pipeline time and improved error isolation. Enforced branch protection and mandatory peer reviews.

## Document Analyzer (AI Guild Hackathon) — Ollama, Node.js, Docker
Proof of concept for a containerized, local LLM document analyzer designed for high-privacy research environments (team of 6). Architected a system to index documentation into searchable segments for TU Delft research staff.

## AI Cup (Team Epoch) — Python, XGBoost, Random Forest
Classification model identifying 9 bird species from radar data to mitigate bird-strike risks at wind farms. Implemented an ensemble approach (XGBoost + Random Forest) processing high-dimensional radar telemetry, optimized for Mean Average Precision.

## Local AI Stack — Ollama, Gemma 4, OpenClaw
Personal setup running Gemma 4 E4B (Q4_K_M quantization, 64K context) locally on CPU via Ollama with custom sampling parameters. Connected to OpenClaw agent with a Telegram interface. Planning VPS deployment for always-on hosting.

# Notable Experiences

- **CERN HSSIP-RO (2024):** Selected as one of 24 students from all of Romania for a 2-week study program at CERN in Geneva. Presented antimatter research.
- **NSS Space Settlement Contest:** Won 2nd place (10th grade) and 4th place (11th grade) out of 5000+ global entries. Presented at ISDC conferences in Frisco, TX and Los Angeles, CA.
- **Dr. Randall Perry Quiet Leadership Award:** Central lead for a 28-member international team at the European Space Design Competition. Managed cross-departmental integration across 4 global sub-teams during a 48-hour competition.
- **Royal Foundation Princess Margareta (volunteer):** Taught math, CS, Romanian, and English to children from underprivileged backgrounds (grades 6–12). Gamified CS concepts using Scratch.

# Languages

- **English:** C2 (fluent, all professional work conducted in English)
- **Romanian:** Native

# Interests & Personality

I gravitate toward building things that solve my own problems — the internship bot, the local AI stack, the non-profit. I'm comfortable in client-facing and cross-cultural settings (ran meetings with Turkish, British, and Romanian stakeholders during my UiPath internship). I'm direct, I learn fast, and I'd rather ship something imperfect and iterate than over-plan.

Music: frequent concert-goer. I care about teams with good energy.