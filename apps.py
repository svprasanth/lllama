from logging import exception
import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import ollama
import os
from  time import *
import subprocess
import  sys
import  contextlib




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
    region_filter = st.sidebar.multiselect("Filter by Region:", customer_data["Region"].unique(), default=customer_data["Region"].unique())
    category_filter = st.sidebar.multiselect("Filter by Product Category:", customer_data["Product_Category"].unique(), default=customer_data["Product_Category"].unique())

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
    fig_sales_category = px.bar(sales_by_category, x="Product_Category", y="Sales_Amount", title="Sales by Product Category")
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
                    summary_context ="\n".join([f"{key}: {value}" for key, value in data_summary.items()])
                    response = ollama.chat(model="llama3.2-vision",
                     messages=[
                        {"role": "system", "content": "You are an AI assistant. Use the data context provided to answer questions."},
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



# Launch the Streamlit app
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
    command = f"streamlit run apps.py --browser.serverAddress=localhost --server.runOnSave=false"
    command1=f"ollama serve"
    with SuppressStdoutAndStderr():
        if __name__ == "__main__":
            # Launch Streamlit app
            subprocess.Popen(command, shell=True)  # Non-blocking, allows browser tab to open
            subprocess.Popen(command1, shell=True)  # Non-blocking, allows browser tab to open
            
            
            sleep(5)  # Give Streamlit time to initialize
            print("Streamlit app launched in browser!")
except OSError as e :
    print(f"An error occurred while launching the Streamlit app:")
    print("Please check the file path and command syntax.")