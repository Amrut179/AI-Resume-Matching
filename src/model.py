import re
import os
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.file_helper import get_resume_text
from src.debugger import print_pipeline

# Create a synonym dictionary
synonym_dict = {
    "ml": ["machine learning"],
    "analysis": ["analytics"],
    "ror": ["ruby", "ruby on rails", "rails", "rail"],
    "ruby": ["ruby", "ruby on rails"],
    "javascript": ["js", "java script", "ecmascript", "client-side scripting"],
    "js": ["js", "java script", "ecmascript", "client-side scripting"],
    "react": ["reactjs", "react.js"]
    # Add more synonyms as needed
}

# Load spaCy's pre-trained English model
nlp = spacy.load("en_core_web_sm")
skills_nlp = spacy.blank("en")

# create custom entity ruler with training data from https://github.com/kingabzpro/jobzilla_ai/blob/main/jz_skill_patterns.jsonl
ruler = skills_nlp.create_pipe('entity_ruler')
ruler.from_disk("data/skillsets.jsonl")
skills_nlp.add_pipe(ruler)


def process_text(text):
    text = text.lower()
    text = text.replace("\n", " ")
    text = re.sub(r'\s+', ' ', text)

    doc = nlp(text)
    # print("=================== remove extra spaces and lower =========================")
    # print(text)
    # print_pipeline(doc)
    tokens = []

    for token in doc:
        if not token.is_stop and not token.is_punct:
            tokens.append(token.lemma_.lower())

    return tokens

# Tokenize and preprocess text using spaCy and NLTK
def fetch_uniq_skills(jd_tokens):
    job_description = " ".join(jd_tokens)

    doc = skills_nlp(job_description)
    skills = []

    for token in doc.ents:
        if token.label_ == "SKILL":
            skill = token.lemma_.lower()
            if skills.count(skill) == 0:
                skills.append(skill) 
 
    return skills

# Function to expand synonyms
def expand_synonyms(tokens):
    expanded_tokens = []
    for token in tokens:
        expanded_tokens.append(token)
        if token in synonym_dict:
            expanded_tokens.extend(synonym_dict[token])
    return expanded_tokens

def remove_duplicate_words(string):
    x = string.split()
    x = sorted(set(x), key = x.index)
    return ' '.join(x)

# Function to extract candidate information from a resume
def extract_candidate_info(text):
    candidate_email = ""
    candidate_phone = ""

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    phone_pattern = r'\b(?:\+\d{1,2}\s?)?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{4}\b'
    experience_pattern = r'(\d+(\.\d+)?)(?:\s?(\+)?\s?(year|yr|yrs|month|mnth|mo)s?)?'

    # Extract email using regex
    email_match = re.search(email_pattern, text)
    if email_match:
        candidate_email = email_match.group()

    # Extract phone number using regex
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        candidate_phone = phone_match.group()

    # Extract all sentences that mention experience
    doc = nlp(text)
    experience_sentences = [sent.text for sent in doc.sents if re.search(experience_pattern, sent.text, re.IGNORECASE)]
    total_experience_years = 0
    total_experience_months = 0

    # Parse and accumulate years of experience from the extracted sentences
    for sentence in experience_sentences:
        matches = re.findall(experience_pattern, sentence, re.IGNORECASE)
        for match in matches:
            exp_text, _, plus_sign, unit = match
            exp_text = exp_text.strip()
            numeric_part = exp_text.split()[0]
            try:
                float_value = float(numeric_part)
            except ValueError:
                print("The string does not contain a valid numeric value.")
            if numeric_part:
                years = float(numeric_part)
                if plus_sign:  # Check if the plus sign is present
                    years += 1  # Add 1 year if there's a plus sign
            if unit and (unit in ("year", "yr", "yrs")):
                total_experience_years += years
            elif unit and (unit in ("month", "mnth", "mo")):
                total_experience_months += years
        formatted_experience = (
            f"{int(total_experience_years)} {'year' if total_experience_years == 1 else 'years'}, "
            f"{int(total_experience_months)} {'month' if total_experience_months == 1 else 'months'}"
        )
        if total_experience_years + total_experience_months == 0:
            formatted_experience = '-'

    return {
        "email": candidate_email,
        "phone": candidate_phone,
        "experience": formatted_experience,
        "accuracy": 0,
        "common_skills": []
    }

# Function to calculate cosine similarity between two texts
def calculate_cosine_similarity(text1, text2):
    vectors = TfidfVectorizer().fit_transform([text1, text2])
    return cosine_similarity([vectors[0]], [vectors[1]])[0][0]

def calculate_weighted_accuracy(jd_skills, common_skills):
    weighted_accuracy = 0.0
    jd_skills = list(jd_skills)

    for skill in common_skills:
        if skill in jd_skills:
            # Assign a higher weight to skills based on their index in js_skills
            weight = 1.0 / (1 + (jd_skills.index(skill) / 10))  # Inverse of the index
            weighted_accuracy += weight
            print(f"{skill}: {weight}")
    
    # Normalize the weighted accuracy by dividing by the sum of weights
    total_weight = sum(1.0 / (1 + (jd_skills.index(skill) / 10)) for skill in jd_skills)
    print(total_weight)
    
    accuracy = (weighted_accuracy / total_weight) * 100 if total_weight > 0 else 0.0
    return accuracy

# Function to match a resume with a job description
def match_resume_with_job_description(resume_text, job_description):
    # Process resume text
    resume_tokens = process_text(resume_text)
    resume_tokens = expand_synonyms(resume_tokens)

    # Preprocess JD
    jd_tokens = process_text(job_description)
    jd_tokens = fetch_uniq_skills(jd_tokens)

    # try to fetch info like email and phone from resume
    info = extract_candidate_info(resume_text.lower())
    common_skills = list(set(filter(lambda x: x in jd_tokens, resume_tokens)))

    accuracy = calculate_weighted_accuracy(jd_tokens, common_skills)

    info["jd_skills"] = jd_tokens
    info["common_skills"] = common_skills
    info["accuracy"] = accuracy
    info["name"] = ''

    return info

def match(resume_path, job_description):
    # resume_path = 'resume.pdf'
    # job_description = "Bachelor's or Master’s degree in Computer Science, Engineering or related field, or equivalent training, fellowship, or work experience A track record of approximately 8+ years of solving platform-level problems for multiple teams across the stack by building and delivering production quality software systems Excellent communication skills: Clear written and oral communication is important to our ability to operate as a remote team and in building our relationship with our cross-functional partners Strong sense of ownership and customer empathy: Our mission is to create a seamless customer experience; understanding the intricacies of the customer journey and being proactive about doing right by our customers is critical to our success. Strong engineering fundamentals: we value transferable experience writing & debugging code, scaling existing services, and designing/architecting software systems. Proven expertise in their technology of choice. Ideally full-stack development experience using React, GraphQL, Ruby, Golang, ElasticSearch, and PostgresSQL."
    resume_text = get_resume_text(resume_path)
    data = match_resume_with_job_description(resume_text, job_description)
    data["name"] = resume_path.replace('uploads/','')

    print(f"info: {data}")
    return data

# if __name__ == "__main__":
#     match('','')
