import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import ollama

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
