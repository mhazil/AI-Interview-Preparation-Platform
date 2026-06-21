from flask import Flask, render_template, request
from PyPDF2 import PdfReader
from openai import OpenAI
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():

    role = request.form["role"]
    resume = request.files.get("resume")

    resume_text = ""

    if resume and resume.filename:

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            resume.filename
        )

        resume.save(filepath)

        reader = PdfReader(filepath)

        for page in reader.pages:
            text = page.extract_text()
            if text:
                resume_text += text

    # ---------- SKILL EXTRACTION ----------

    skill_prompt = f"""
    Extract only technical skills from this resume.

    Resume:
    {resume_text}

    Return only comma separated skills.

    Example:
    Python, Java, SQL, HTML, CSS, Git
    """

    skill_response = client.chat.completions.create(
        model="llama-3.2-1b-instruct",
        messages=[
            {"role": "user", "content": skill_prompt}
        ]
    )

    skills_text = skill_response.choices[0].message.content

    skills = []

    for skill in skills_text.split(","):

        skill = skill.strip()

        if len(skill) < 25:
            skills.append(skill)

    # ---------- QUESTION GENERATION ----------

    question_prompt = f"""
    Candidate Role: {role}

    Skills:
    {', '.join(skills)}

    Generate exactly 10 interview questions.

    Rules:
    - One question per line
    - No numbering
    - No introduction
    - No explanation
    """

    question_response = client.chat.completions.create(
        model="llama-3.2-1b-instruct",
        messages=[
            {"role": "user", "content": question_prompt}
        ]
    )

    questions_text = question_response.choices[0].message.content

    questions = []

    for line in questions_text.split("\n"):

        line = line.strip()

        if (
            line
            and "Here are" not in line
            and "interview questions" not in line
            and len(line) > 10
        ):
            questions.append(line)

    return render_template(
        "result.html",
        role=role,
        skills=skills,
        questions=questions
    )

@app.route("/evaluate", methods=["POST"])
def evaluate():

    question = request.form["question"]
    answer = request.form["answer"]

    evaluation_prompt = f"""
    Question:
    {question}

    Candidate Answer:
    {answer}

    Evaluate the answer.

    Give:

    Score: /10

    Strengths:
    -

    Improvements:
    -

    Ideal Answer:
    -
    """

    response = client.chat.completions.create(
        model="llama-3.2-1b-instruct",
        messages=[
            {"role": "user", "content": evaluation_prompt}
        ]
    )

    feedback = response.choices[0].message.content

    return render_template(
        "feedback.html",
        question=question,
        answer=answer,
        feedback=feedback
    )

if __name__ == "__main__":
    app.run(debug=True)