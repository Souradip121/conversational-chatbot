import sqlite3
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
import os

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = ""

# Initialize the GPT model
llm = ChatOpenAI(model="gpt-4")

# Function to classify the category of the grievance
def gpt_classify_category(grievance_input):
    categories = [
        "Medical Assistance", "Security", "Divyangjan Facilities", 
        "Facilities for Women with Special Needs", "Electrical Equipment", 
        "Coach Cleanliness", "Punctuality", "Water Availability", 
        "Coach Maintenance", "Catering & Vending Services", 
        "Staff Behaviour", "Corruption/Bribery", "Bed Roll", 
        "Miscellaneous"
    ]
    
    prompt_template = """
    Classify the following grievance into one of the following categories:
    {categories}
    
    Grievance: "{input}"
    
    Category:
    """
    
    prompt = PromptTemplate(
        input_variables=["input", "categories"],
        template=prompt_template
    )
    
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    response = llm_chain.run({"input": grievance_input, "categories": ", ".join(categories)})
    return response.strip()

# Function to generate follow-up questions based on the category
def gpt_generate_followup_questions(grievance_input, category):
    prompt_template = """
    Based on the following grievance in the category "{category}", generate 3-4 follow-up questions.
    
    Grievance: "{input}"
    
    Questions:
    """
    
    prompt = PromptTemplate(
        input_variables=["input", "category"],
        template=prompt_template
    )
    
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    response = llm_chain.run({"input": grievance_input, "category": category})
    return response.strip().split("\n")

# Function to identify whether it's a train or station-related query
def gpt_identify_train_or_station(grievance_input):
    prompt_template = """
    Identify whether the following grievance is related to a train or station:
    
    Grievance: "{input}"
    
    Response (Train/Station):
    """
    
    prompt = PromptTemplate(
        input_variables=["input"],
        template=prompt_template
    )
    
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    response = llm_chain.run({"input": grievance_input})
    return response.strip()

# Function to check if the grievance is goods-related
def gpt_is_goods_related(grievance_input):
    prompt_template = """
    Is the following grievance related to goods (Yes/No)?
    
    Grievance: "{input}"
    
    Response:
    """
    
    prompt = PromptTemplate(
        input_variables=["input"],
        template=prompt_template
    )
    
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    response = llm_chain.run({"input": grievance_input})
    return response.strip().lower() == "yes"

# Function to store grievance data in the SQLite database
def store_in_database(grievance_data):
    # Connect to SQLite database (or create one if it doesn't exist)
    conn = sqlite3.connect('railmadad_grievances.db')
    cursor = conn.cursor()

    # Create a table for storing grievance data if it doesn't already exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS grievances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grievance TEXT NOT NULL,
        category TEXT NOT NULL,
        train_or_station TEXT NOT NULL,
        pnr TEXT,
        date TEXT,
        time TEXT,
        follow_up_responses TEXT
    )
    ''')

    # Insert the grievance data into the database
    cursor.execute('''
    INSERT INTO grievances (grievance, category, train_or_station, pnr, date, time, follow_up_responses)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (grievance_data["grievance"], grievance_data["category"], grievance_data["train_or_station"], 
          grievance_data.get("pnr"), grievance_data.get("date"), grievance_data.get("time"), 
          grievance_data["follow_up_responses"]))

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print("Grievance data successfully stored in the database.")

# Main chatbot function for RailMadad
def railmadad_chatbot():
    grievance_data = {"follow_up_responses": []}

    # Collect the initial grievance
    grievance_input = input("Please describe your grievance: ")
    grievance_data["grievance"] = grievance_input

    # Check if the grievance is related to goods
    is_goods_related = gpt_is_goods_related(grievance_input)

    if is_goods_related:
        # If goods-related, ask for a detailed description
        goods_description = input("Please provide a detailed description of the issue with the goods: ")
        grievance_data["category"] = "Goods Related"
        grievance_data["follow_up_responses"] = goods_description
        print("\nThank you for providing the information about the goods-related grievance.")
    else:
        # Classify the grievance into a category
        category = gpt_classify_category(grievance_input)
        grievance_data["category"] = category
        print(f"Grievance classified under: {category}")

        # Identify whether the grievance is train-related or station-related
        train_or_station = gpt_identify_train_or_station(grievance_input)
        grievance_data["train_or_station"] = train_or_station
        print(f"Grievance related to: {train_or_station}")

        # Ask for PNR if it's a train-related issue
        if train_or_station.lower() == "train":
            grievance_data["pnr"] = input("Please provide your PNR number (if available): ")
        
        # Ask for date and time of the incident
        grievance_data["date"] = input("Please provide the date of the incident (DD-MM-YYYY): ")
        grievance_data["time"] = input("Please provide the time of the incident (HH:MM): ")

        # Generate follow-up questions based on the category
        follow_up_questions = gpt_generate_followup_questions(grievance_input, category)

        # Loop through follow-up questions and collect responses as question:answer pairs
        follow_up_response_pairs = []
        for question in follow_up_questions:
            print(question)
            follow_up_response = input("Your response: ")
            follow_up_response_pairs.append(f"{question.strip()}: {follow_up_response.strip()}")
        
        # Store the follow-up responses as a single string in the format "Question: Answer"
        grievance_data["follow_up_responses"] = "; ".join(follow_up_response_pairs)

    # Display the final information collected
    print("\nThank you! Here's the information collected:")
    for key, value in grievance_data.items():
        if key != "follow_up_responses":
            print(f"{key.capitalize()}: {value}")
    print("Follow-up responses:", grievance_data["follow_up_responses"])

    # Store the data in the database
    store_in_database(grievance_data)

# Run the chatbot for RailMadad
railmadad_chatbot()
