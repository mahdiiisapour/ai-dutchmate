import streamlit as st
from openai import OpenAI
import os

# ---- Setup ----
st.set_page_config(page_title="DutchMate 🇳🇱", page_icon="🇳🇱")
st.title("🇳🇱 DutchMate – Your AI Dutch Tutor")

# OpenAI Client Setup (Replace with your actual key or load via dotenv)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"))

# Sidebar
option = st.sidebar.selectbox("Choose an activity", [
    "📝 Word of the Day",
    "❓ Vocab Quiz"
])

# ---- Word of the Day ----
if option == "📝 Word of the Day":
    st.subheader("Word of the Day")

    # Initialize history if it doesn't exist
    if 'word_history' not in st.session_state:
        st.session_state.word_history = []
    
    if 'word_output' not in st.session_state:
        st.session_state.word_output = None

    # Modified prompt to include instruction to avoid previously shown words
    prompt = """
    Give me a random, common Dutch word that is appropriate for a beginner at the A2 level.
    IMPORTANT: DO NOT use any of these words that have been shown before: {}.
    Please include:
    - A mix of word types: nouns, verbs, adjectives, etc.
    - The English translation of the word.
    - A fun fact or cultural tidbit about the word or its usage in Dutch culture.
    Format:
    Word: [Dutch word]
    Translation: [English translation]
    Fun fact: [Fun fact or cultural tidbit]
    """.format(", ".join(st.session_state.word_history))

    # If the word is not fetched yet or the user clicked "Get Word" to fetch a new word
    if st.button("Get Word") or st.session_state.word_output is None:
        with st.spinner("Fetching your word..."):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            word_output = response.choices[0].message.content
            
            # Extract the Dutch word from the response
            try:
                lines = word_output.split('\n')
                for line in lines:
                    if line.startswith("Word:"):
                        dutch_word = line.split("Word:")[1].strip()
                        # Add only the Dutch word to history
                        st.session_state.word_history.append(dutch_word)
                        # Limit history to last 50 words to keep prompt size manageable
                        if len(st.session_state.word_history) > 50:
                            st.session_state.word_history = st.session_state.word_history[-50:]
                        break
            except:
                # If parsing fails, just continue
                pass
                
            # Format and display the output
            formatted_output = word_output.replace("Word:", "\n**Word:**").replace("Translation:", "\n**Translation:**").replace("Fun fact:", "\n**Fun fact:**")
            st.session_state.word_output = formatted_output
            st.markdown(formatted_output)

    elif st.session_state.word_output:
        # Display previously fetched word if it exists in session state
        st.markdown(st.session_state.word_output)

# ---- Vocab Quiz ----
elif option == "❓ Vocab Quiz":
    st.subheader("Dutch Vocab Quiz")

    if "quiz_generated" not in st.session_state:
        st.session_state.quiz_generated = False
    
    # Initialize quiz history if it doesn't exist
    if 'quiz_word_history' not in st.session_state:
        st.session_state.quiz_word_history = []

    if st.button("Generate Quiz") or not st.session_state.quiz_generated:
        quiz_prompt = """
        Create one beginner-friendly Dutch vocabulary quiz question.
        IMPORTANT: DO NOT use any of these Dutch words that have been shown before: {}.
        Include:
        - The Dutch word (choose common words useful for A2 level)
        - 4 multiple choice options (A, B, C, D) with only one correct English meaning
        - Mark the correct answer
        Format:

        Word: [Dutch word]
        What does it mean?
        A. [English option]
        B. [English option]
        C. [English option]
        D. [English option]
        Answer: [Correct letter only]
        """.format(", ".join(st.session_state.quiz_word_history))

        with st.spinner("Generating quiz question..."):
            quiz_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": quiz_prompt}]
            )
            content = quiz_response.choices[0].message.content.strip().split("\n")

        try:
            word_line = [line for line in content if line.startswith("Word:")][0]
            word = word_line.split(":", 1)[1].strip()
            
            # Add word to quiz history
            st.session_state.quiz_word_history.append(word)
            # Limit history to last 50 words
            if len(st.session_state.quiz_word_history) > 50:
                st.session_state.quiz_word_history = st.session_state.quiz_word_history[-50:]
                
            # Find the question line
            question_idx = 0
            for i, line in enumerate(content):
                if "What does it mean?" in line:
                    question_idx = i
                    break
            question = content[question_idx].strip()
            
            # Get choices (should be the 4 lines after the question)
            choices_raw = content[question_idx+1:question_idx+5]
            
            # Find the answer line
            answer_line = [line for line in content if line.startswith("Answer:")][0]
            correct = answer_line.split(":", 1)[1].strip().upper()

            options_dict = {
                line.split(".")[0].strip(): line.split(".", 1)[1].strip()
                for line in choices_raw
            }

            st.session_state.word = word
            st.session_state.question = question
            st.session_state.options_dict = options_dict
            st.session_state.correct = correct
            st.session_state.quiz_generated = True
            st.session_state.user_answer = None
            st.session_state.answered = False

        except Exception as e:
            st.error(f"⚠️ Failed to parse quiz. Try again. Error: {e}")
            st.session_state.quiz_generated = False

    if st.session_state.get("quiz_generated", False):
        st.markdown(f"**Word:** {st.session_state.word}")
        st.markdown(f"**{st.session_state.question}**")

        # Display the options in a clear, readable format
        for option, choice in st.session_state.options_dict.items():
            st.markdown(f"**{option}.** {choice}")

        # Add radio buttons for the user to choose an answer
        user_choice = st.radio("Choose your answer:", list(st.session_state.options_dict.keys()), key="user_answer")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Submit Answer"):
                st.session_state.answered = True
                if user_choice == st.session_state.correct:
                    st.success("✅ Correct!")
                else:
                    # Use the correct letter to access the correct answer
                    correct_answer = st.session_state.correct
                    correct_meaning = st.session_state.options_dict[correct_answer]
                    st.error(f"❌ Incorrect. The correct answer was **{correct_answer}**: {correct_meaning}")
        
        with col2:
            if st.button("Try Another Question"):
                st.session_state.quiz_generated = False
                st.experimental_rerun()

# Add a footer
st.markdown("---")
st.markdown("DutchMate - Learn Dutch the fun way! 🧀🌷")