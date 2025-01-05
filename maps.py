import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from folium.plugins import MarkerCluster
import datetime
from streamlit.components.v1 import html

# Load the CSV file from Google Drive
file_path = '/content/drive/MyDrive/Dataset/cleaned_data_with_cluster.csv'  # Replace with your actual file path
df = pd.read_csv(file_path)

# Ensure the 'Order Creation Date' column is in datetime format (column 5, index 4)
df.iloc[:, 4] = pd.to_datetime(df.iloc[:, 4], errors='coerce', format='%d/%m/%Y %H:%M')

st.title('HappyTupper Customer Clustering')

# Add explanations about the clusters in the sidebar
st.sidebar.header("Cluster Explanations")
cluster_explanations = {
    0: "Cluster 0: High Value, Loyal Customers.",
    1: "Cluster 1: High Value, Occasional Buyers",
    2: "Cluster 2: Low Value, Voucher-Driven Buyers",
    3: "Cluster 3: Infrequent, Low-Value Purchasers",
    4: "Cluster 4: New Buyers with Moderate Frequency",
    5: "Cluster 5: Low-Value, Frequent Buyers"
}

# Display the explanations in the sidebar
for cluster_id, explanation in cluster_explanations.items():
    st.sidebar.markdown(f"**{cluster_id}**: {explanation}")

# Step 1: Add Date Filter (Time Series Adjustment)
if 'Order Creation Date' in df.columns:
    # Get min and max date from the dataset
    min_date = df['Order Creation Date'].min().to_pydatetime()
    max_date = df['Order Creation Date'].max().to_pydatetime()

    # Step 2: Create a date range slider for filtering the data
    start_date, end_date = st.slider(
        "Select Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )

    # Step 3: Filter the data based on the selected date range and remove 'Cancelled' orders
    filtered_df = df[(df['Order Creation Date'] >= start_date) &
                     (df['Order Creation Date'] <= end_date) &
                     (df['Order Status'] != 'Cancelled')]

    # Show the filtered data
    st.write(f"Selected data from {start_date} to {end_date}")
    st.dataframe(filtered_df)

    # Step 4: Calculate required metrics
    total_customers = filtered_df['Username (Buyer)'].nunique()  # Assuming 'Customer ID' is the customer identifier
    total_purchase_amount = filtered_df['Total Amount'].sum()  # Assuming 'Total Amount' is the purchase amount column
    total_voucher_usage = filtered_df[filtered_df['Voucher'] == 1].shape[0] #Calculate Total Voucher Usage (count where Voucher == 1)

    # Breakdown by KMeans_Cluster
    cluster_breakdown = filtered_df['KMeans_Cluster'].value_counts().reset_index()
    cluster_breakdown.columns = ['Cluster ID', 'Number of Customers']

    # Step 5: Set up side-by-side layout using st.columns
    col1, col2 = st.columns([1, 1])  # Create two columns of equal width

    card_style = """
        <div style="padding: 10px; border-radius: 8px; text-align: center; height: 120px;">
            <p style="font-size: 26px; font-weight: bold; color: skyblue; margin-bottom: 5px;">{}</p>
            <h4 style="font-size: 14px; font-weight: normal; color: darkgrey; margin-top: 10px;">{}</h4>
        </div>
    """

    # Create cards for Total Customers, Total Purchase Amount, Total Voucher Usage
    with col1:
        st.markdown(card_style.format(f"{total_customers:,.0f}", "Total Customers"), unsafe_allow_html=True)
        st.markdown(card_style.format("${:,.2f}".format(total_purchase_amount), "Total Purchase Amount"), unsafe_allow_html=True)
        st.markdown(card_style.format(f"{total_voucher_usage:,.0f}", "Total Voucher Usage"), unsafe_allow_html=True)

    # Right column - Pie chart for Cluster Breakdown
    with col2:
        # Create the Pie chart for the cluster breakdown
        plt.figure(figsize=(6, 6))

        # Handle cases where the cluster breakdown might be empty
        if not cluster_breakdown.empty:
            plt.pie(cluster_breakdown['Number of Customers'],
                    labels=cluster_breakdown['Cluster ID'].astype(str),
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=plt.cm.Paired.colors)
            plt.title("Customer Distribution by Cluster")

            # Fix to ensure the pie chart is rendered properly in Streamlit
            st.pyplot(plt.gcf())  # Using plt.gcf() to ensure we plot the correct figure object
        else:
            st.write("No data available for the selected period.")

    # --- Add the Folium Map for Clustering ---
    # Create the base map centered around Singapore
    map_center = [1.3521, 103.8198]  # Singapore's latitude and longitude
    folium_map = folium.Map(location=map_center, zoom_start=12)

    # Create a MarkerCluster
    marker_cluster = MarkerCluster().add_to(folium_map)

    # Define color for each cluster (6 clusters)
    cluster_colors = {
        0: 'red',
        1: 'blue',
        2: 'green',
        3: 'purple',
        4: 'orange',
        5: 'yellow'
    }

    # Add markers to the map based on the filtered data
    for _, row in filtered_df.iterrows():
        lat = row['Lat']
        lon = row['Log']
        cluster = row['KMeans_Cluster']

        # Get the corresponding color for the cluster
        cluster_color = cluster_colors.get(cluster, 'gray')

        # Add a circle marker for each customer location
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            color=cluster_color,
            fill=True,
            fill_color=cluster_color,
            fill_opacity=0.6,
            popup=f"Order ID: {row['Order ID']}<br>Category: {row['Category']}<br>Total Amount: {row['Total Amount']}"
        ).add_to(marker_cluster)

    # Step 6: Save the Folium map to an HTML file
    map_filename = "customer_clustering_map.html"
    folium_map.save(map_filename)

    # Step 7: Render the Folium map in the Streamlit app
    # Convert the Folium map to HTML and embed it in Streamlit
    map_html = folium_map._repr_html_()
    html(map_html, height=1000)

else:
    st.error("The dataset does not contain a 'Order Creation Date' column.")
