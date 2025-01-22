from logging import exception
import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import ollama
import os
from time import *
import subprocess
import sys
import contextlib
# Load the uploaded customer data file
uploaded_file = st.sidebar.file_uploader("Upload Customer Data (Excel):", type=["xlsx"])

if uploaded_file:
    customer_data = pd.read_excel(uploaded_file)
    st.sidebar.success("Customer data loaded successfully!")

    # Display dataset overview
    st.subheader("Customer Data Overview")
    st.dataframe(customer_data)

    # Sidebar filters
    st.sidebar.header("Customer Data Filters")
    region_filter = st.sidebar.multiselect("Filter by Region:", customer_data["Region"].unique(),
                                           default=customer_data["Region"].unique())
    category_filter = st.sidebar.multiselect("Filter by Product Category:", customer_data["Product_Category"].unique(),
                                             default=customer_data["Product_Category"].unique())

    filtered_data = customer_data[(customer_data["Region"].isin(region_filter)) &
                                  (customer_data["Product_Category"].isin(category_filter))]


    # Generate data summary
    def generate_data_summary(data):
        sales_summary = data.groupby("Product_Category")["Sales_Amount"].sum().to_dict()
        region_summary = data.groupby("Region")["Sales_Amount"].sum().to_dict()
        churn_distribution = data["Churn_Risk"].value_counts().to_dict()
        satisfaction_avg = data.groupby("Region")["Satisfaction_Score"].mean().to_dict()

        summary = {
            "Total Sales by Product Category": sales_summary,
            "Total Sales by Region": region_summary,
            "Churn Risk Distribution": churn_distribution,
            "Average Satisfaction Score by Region": satisfaction_avg,
            "Total Number of Records": data
        }
        return summary


    data_summary = generate_data_summary(filtered_data)

    # Sales Analysis
    st.subheader("Sales Analysis")
    sales_by_category = filtered_data.groupby("Product_Category")["Sales_Amount"].sum().reset_index()
    fig_sales_category = px.bar(sales_by_category, x="Product_Category", y="Sales_Amount",
                                title="Sales by Product Category")
    st.plotly_chart(fig_sales_category)

    sales_by_region = filtered_data.groupby("Region")["Sales_Amount"].sum().reset_index()
    fig_sales_region = px.bar(sales_by_region, x="Region", y="Sales_Amount", title="Sales by Region")
    st.plotly_chart(fig_sales_region)

    # AI-Powered Chatbot Section
    st.subheader("AI-Powered Chatbot")
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_question = st.text_input("Ask a question:")

    # Button to process the question
    if st.button("Ask AI"):
        if user_question:
            with st.spinner("Generating response, please wait..."):
                try:
                    # Include data summary in the context
                    summary_context = "\n".join([f"{key}: {value}" for key, value in data_summary.items()])
                    response = ollama.chat(model="llama3.2-vision",
                                           messages=[
                                               {"role": "system",
                                                "content": "You are an AI assistant. Use the data context provided to answer questions."},
                                               {"role": "user", "content": f"Data Context:\n{summary_context}"},
                                               {"role": "user", "content": f"Question: {user_question}"}])

                    # Append user question and AI response to the chat history
                    st.session_state["chat_history"].append({
                        "question": user_question,
                        "answer": response["message"]["content"]
                    })
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.warning("Please enter a question before clicking the button.")

    # Display chat history
    st.subheader("Chat History")
    for chat in st.session_state["chat_history"]:
        st.markdown(f"**You:** {chat['question']}")
        st.markdown(f"**vivekda05** {chat['answer']}")


class SuppressStdoutAndStderr:
    def __enter__(self):
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self.stdout
        sys.stderr = self.stderr
def install_and_download_ollama():
    try:
        # Step 1: Check if 'ollama' is installed
        check_cmd = ["ollama", "--version"]
        subprocess.run(check_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("Ollama is already installed.")
    except subprocess.CalledProcessError:
        # Step 2: Install 'ollama' if not installed
        print("Ollama not found. Installing now...")
        if sys.platform == "win32":
            install_cmd = ["winget", "install", "-e", "--id", "Ollama.Ollama"]
        elif sys.platform == "darwin":  # macOS
            install_cmd = ["/bin/bash", "-c", "$(curl -fsSL https://ollama.com/install.sh)"]
        else:
            raise OSError("Ollama installation is only supported on Windows and macOS.")

        subprocess.run(install_cmd, check=True)
        print("Ollama installed successfully.")

# Launch the Streamlit app
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
    command = f"streamlit run streamlit_app.py --server.port=8501 --browser.serverAddress=localhost --server.runOnSave=false"
    with SuppressStdoutAndStderr():
        if __name__ == "__main__":
            install_and_download_ollama()
            pull_cmd = ["ollama", "pull", "llama3.2-vision"]
            subprocess.run(pull_cmd)
            # Launch Streamlit app
            subprocess.Popen(command, shell=True)  # Non-blocking, allows browser tab to open
            sleep(3)  # Give Streamlit time to initialize
            print("Streamlit app launched in browser!")
except exception as e:
    print(f"An error occurred while launching the Streamlit app:")
    print("Please check the file path and command syntax.")