from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field


class JobEvaluation(BaseModel):
    is_match: bool = Field(description="Whether the job is a good fit for the user based on their resume and preferences.")
    match_reason: str = Field(description="A single sentence explaining why the user is a great fit, to be used in an outreach message. If not a match, this can be empty.")
    target_titles: list[str] = Field(description="A list of 2-3 job titles at this company that would be best to message (e.g., 'Technical Recruiter', 'Engineering Manager').")

def evaluate_job(job, config):
    """
    Evaluates a job description against the user's resume using LLM.
    Returns a JobEvaluation object.
    """
    print(f"Evaluating job: {job['title']} at {job['company']}")
    
    # Check if we have API key
    if not config.GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not set. Falling back to default match.")
        return JobEvaluation(
            is_match=True,
            match_reason="I have the relevant skills for this role.",
            target_titles=["Recruiter", "Hiring Manager"]
        )

    llm = ChatGoogleGenerativeAI(
        model=config.LLM_MODEL,
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.2
    )
    
    parser = JsonOutputParser(pydantic_object=JobEvaluation)
    
    prompt = PromptTemplate(
        template="""You are an expert career advisor. Evaluate if the following job is a good fit for the user.

USER RESUME:
{resume}

USER PREFERENCES:
{preferences}

JOB TITLE: {job_title}
COMPANY: {company}
JOB DESCRIPTION:
{job_description}

Based on this information, provide:
1. is_match: True if the job aligns with the user's resume and preferences, False otherwise.
2. match_reason: If it's a match, write a single punchy sentence (max 150 characters) explaining why they are a great fit. This will be used in a LinkedIn connection request. 
   Format it so it can be appended to "I'd be a great fit because ". For example: "my 5 years of Python experience perfectly aligns with your backend stack."
3. target_titles: 2-3 job titles (strings) of people at {company} who would be best to reach out to for a referral for this specific role. (e.g., "Engineering Manager", "Technical Recruiter")

\n{format_instructions}""",
        input_variables=["resume", "preferences", "job_title", "company", "job_description"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    
    try:
        # Truncate job description if it's too insanely long to save tokens
        desc = job['description'][:8000] if len(job['description']) > 8000 else job['description']
        
        result = chain.invoke({
            "resume": config.USER_RESUME,
            "preferences": config.USER_PREFERENCES,
            "job_title": job['title'],
            "company": job['company'],
            "job_description": desc
        })
        
        # Pydantic parsing ensures types are correct, but since we use dict from JsonOutputParser
        # we convert it to the Pydantic object
        return JobEvaluation(**result)
        
    except Exception as e:
        print(f"Error evaluating job {job['job_id']} with AI: {e}")
        # Default fallback on error
        return JobEvaluation(
            is_match=False, 
            match_reason="Error during evaluation", 
            target_titles=[]
        )
