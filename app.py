from flask import Flask, render_template, request, redirect, url_for, session, flash , Response ,abort
import pandas as pd
from groq import Groq
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os

app = Flask(__name__)
app.secret_key = 'ThisIsASecretKey' 

client = Groq(
        api_key= "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",
        )

# Path to store user data
USER_DATA_FILE = 'user_data.csv'
conversation_data = "conversation.csv"

if not os.path.exists(USER_DATA_FILE):
    df = pd.DataFrame(columns=['email', 'username', 'password'])
    df.to_csv(USER_DATA_FILE, index=False)

if not os.path.exists(conversation_data):
    df = pd.DataFrame(columns=['email', 'user_query', 'bot_response'])
    df.to_csv(conversation_data, index=False)
    
# Loading an embedding model 
print("Loading Embeddings Model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
documents = []
# Read Medical Data from file
with open("medical_file.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:
    line = line.strip()
    if line: 
        documents.append(line)

# Generate embeddings for the documents
doc_embeddings = model.encode(documents)
print("Embeddings model loaded and words converted to vectors succesfully.\n")


# Function to load users from CSV
def load_users():
    return pd.read_csv(USER_DATA_FILE)

# Function to save new users to CSV
def save_user(email, username, password):
    df = load_users()
    new_user = pd.DataFrame({'email': [email], 'username': [username], 'password': [password]})
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USER_DATA_FILE, index=False)
    
    df2 = pd.read_csv(conversation_data)
    new_con = pd.DataFrame({'email': [email], 'user_query': "", 'bot_response': f"Hello {username}, I am here to assist you with your Mental Health. How may I be of help?"})
    df2 = pd.concat([df2, new_con], ignore_index=True)
    df2.to_csv(conversation_data, index=False)
    

# Function to save conversation to CSV
def save_conversation(email, query, bot):
    df = pd.read_csv(conversation_data)
    new_conversation = pd.DataFrame({'email': [email], 'user_query': [query], 'bot_response': [bot]})
    df = pd.concat([df, new_conversation], ignore_index=True)
    df.to_csv(conversation_data, index=False)

# Building RAG system
def retrieve_closest_documents(num_closest, user_query):
    # Build FAISS index
    dimension = doc_embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(doc_embeddings))

    query_embedding = model.encode([user_query])

    distances, indices = index.search(np.array(query_embedding), num_closest)

    retrieved_documents = []

    # Check if indices are valid
    for idx in indices[0]:
        if 0 <= idx < len(documents):  
            retrieved_documents.append(documents[idx])
        else:
            print(f"Invalid index: {idx}")

    result_string = "\n".join(retrieved_documents)
    # print("Closest documents:\n", result_string)    
    return result_string

# More context to be added to RAG retrieved context.
context_b = """ICD-10 Depression Diagnostic Criteria
Last Reviewed: 10 Nov 2020

Key Diagnostic Criteria:

- Main Symptoms (At least one must be present for most days over a minimum of 2 weeks):
  - Persistent sadness or low mood
  - Loss of interests or pleasure
  - Fatigue or low energy

- Associated Symptoms (Ask about these if main symptoms are present):
  - Disturbed sleep
  - Poor concentration or indecisiveness
  - Low self-confidence
  - Poor or increased appetite
  - Suicidal thoughts or acts
  - Agitation or slowing of movements
  - Guilt or self-blame

Diagnosis:
The presence of these 10 symptoms determines the degree of depression:
  - Not Depressed: Fewer than four symptoms
  - Mild Depression: Four symptoms
  - Moderate Depression: Five to six symptoms
  - Severe Depression: Seven or more symptoms (with or without psychotic symptoms)

Duration:
Symptoms should be present for a month or more, and each symptom should occur most of every day.
"""

# Get LLM response based on user input and provided context(RAG context & context_b)
def get_response(prompt, data):
    global client
    client = client
    chat_completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "system", "content": f"""You are an AI assistant for Depression Diagnosis, treatments and prognosis for Nigerians. You should show users compassion. 
                   Keep your response very short.\n{data}\n{context_b}"""},
            {"role": "user", "content": prompt}
        ],
        )
    return chat_completion.choices[0].message.content

# Get user conversation history
def get_conversation(email, username):
    df = pd.read_csv(conversation_data)
    df2 = df[df['email'] == email]
    data = """"""
    for query in df2["user_query"]:
        for bot in df2["bot_response"]:
            data += f"""{username}: {query}\nAssistant: {bot}\n"""
    return data


# Landing Page
@app.route('/')
def landing():
    return render_template('landing.html')

# Sign In Page
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Load user data
        users = load_users()

        # Check if the email match any user
        user = users[users['email'] == email] 

        if not user.empty:
            # Now check if the password matches
            if str(user.iloc[0]['password']) == str(password):
                session['user_logged_in'] = True
                session['email'] = email
                session['username'] = user.iloc[0]['username']  # Store the username in session
                return redirect(url_for('chat'))
            else:
                flash('Incorrect Email or Password. Please try again.')
                return redirect(url_for('signin'))
        else:
            flash('User not found. Please Sign Up instead.')
            return redirect(url_for('signin'))
    
    return render_template('signin.html')

# Sign Up Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username') 
        password = request.form.get('password')

        # Load user data
        users = load_users()

        # Check if the email is already registered
        if email in users['email'].values:
            flash('Email already registered. Please sign in.')
            return redirect(url_for('signup'))
        
        save_user(email, username, password)
        
        return redirect(url_for('signin'))

    return render_template('signup.html')

# Sign Out Functionality
@app.route('/signout')
def signout():
    # Remove user session and redirect to landing page
    session.pop('user_logged_in', None)
    session.pop('email', None)
    session.pop('username', None)  
    return redirect(url_for('landing'))

# Chatbot Interaction Page (only accessible if signed in)
@app.route('/chat', methods=['GET'])
def chat():
    if not session.get('user_logged_in'):
        return redirect(url_for('signin'))
    
    username = session.get('username')
    
    return render_template('chat.html', username=username)

# Get and display Assistant's response to Frontend
@app.route('/reply', methods=['POST'])
def reply():
    if request.method == 'POST':
        username = session.get('username')
        email = session.get('email')
        user_input = request.form.get('userInput')
        
        data = get_conversation(email, username)
        data += f"""{username}: {user_input}"""
        
        context_a = retrieve_closest_documents(3, user_input)
        
        bot_respond = get_response(data, context_a)
        
        save_conversation(email, user_input, bot_respond)
        
        return bot_respond
      
# Fetch for user's conversation history and display in frontend       
@app.route('/get_chat_history' , methods=['GET'])
def get_chat_history():
    if session.get('user_logged_in'):
        df = pd.read_csv(conversation_data)
        data = df[df['email'] == session.get('email')]
        data_json = data.to_json(orient='records')
        return data_json
    else:
        return redirect(url_for('signin'))
    
# Delete conversation history
@app.route('/delete_chat' , methods=['GET'])
def delete_chat():
    if session.get('user_logged_in'):
        df = pd.read_csv(conversation_data)
        data = df[df['email'] != session.get('email')]
        data.to_csv( conversation_data , index=False)
        return Response('Success')
     
    return redirect(url_for('signin'))


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
