import aiosqlite
import json
from config import DB_PATH
from models import Job, Question

async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL,
                department TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                discovered_at TEXT NOT NULL DEFAULT (datetime('now')),
                status TEXT NOT NULL DEFAULT 'new'
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL REFERENCES jobs(id),
                label TEXT NOT NULL,
                required INTEGER NOT NULL DEFAULT 0,
                field_type TEXT NOT NULL DEFAULT '',
                options TEXT NOT NULL DEFAULT '[]',
                suggested_answer TEXT NOT NULL DEFAULT ''
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                jobs_found INTEGER NOT NULL DEFAULT 0,
                jobs_new INTEGER NOT NULL DEFAULT 0,
                errors TEXT NOT NULL DEFAULT '[]'
            )
        ''')
        await db.commit()

async def job_exists(job_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT 1 FROM jobs WHERE id = ?', (job_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

async def insert_job(job: Job) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT OR IGNORE INTO jobs (id, company, title, location, url, department, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (job.id, job.company, job.title, job.location, job.url, job.department, job.source))
        await db.commit()

async def insert_questions(job_id: str, questions: list[Question]) -> None:
    if not questions:
        return
        
    async with aiosqlite.connect(DB_PATH) as db:
        data = [
            (job_id, q.label, int(q.required), q.field_type, json.dumps(q.options))
            for q in questions
        ]
        await db.executemany('''
            INSERT INTO questions (job_id, label, required, field_type, options)
            VALUES (?, ?, ?, ?, ?)
        ''', data)
        await db.commit()

async def update_question_answer(question_id: int, answer: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE questions SET suggested_answer = ? WHERE id = ?', (answer, question_id))
        await db.commit()

async def update_job_status(job_id: str, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE jobs SET status = ? WHERE id = ?', (status, job_id))
        await db.commit()

async def log_run(started_at: str, finished_at: str, jobs_found: int, jobs_new: int, errors: list[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO runs (started_at, finished_at, jobs_found, jobs_new, errors)
            VALUES (?, ?, ?, ?, ?)
        ''', (started_at, finished_at, jobs_found, jobs_new, json.dumps(errors)))
        await db.commit()
