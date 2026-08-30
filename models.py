from dataclasses import dataclass, field

@dataclass
class Job:
    id: str                    # unique: f"{company_slug}:{ats_job_id}"
    company: str               # human-readable company name
    title: str
    location: str
    url: str                   # direct apply/view URL
    department: str = ""
    source: str = ""           # "greenhouse", "lever", "smartrecruiters"
    discovered_at: str = ""    # ISO timestamp, set at insert time

@dataclass
class Question:
    job_id: str
    label: str                 # the question text
    required: bool = False
    field_type: str = ""       # "input_text", "textarea", "multi_value_single_select", etc.
    options: list[str] = field(default_factory=list)  # for select-type fields

@dataclass
class Answer:
    question_label: str
    suggested_answer: str
    field_type: str = ""
    is_manual: bool = False    # True for file uploads, checkboxes, etc. that can't be auto-answered
