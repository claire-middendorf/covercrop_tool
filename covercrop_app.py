# -*- coding: utf-8 -*-
"""
Created on Tue May  5 14:11:40 2026

@author: cpmid
"""

#First Attempt at a Streamlit App

import streamlit as st
import pandas as pd
import rasterio
from rasterio.transform import rowcol

RASTER_PATHS = {
    "n_runoff": "https://raw.githubusercontent.com/claire-middendorf/covercrop_tool/main/poorly_drained_nitrogen_runoff_WGS84.tif",
    "n_drain":  "https://raw.githubusercontent.com/claire-middendorf/covercrop_tool/main/poorly_drained_nitrogen_drainflow_WGS84.tif",
    "p_runoff": "https://raw.githubusercontent.com/claire-middendorf/covercrop_tool/main/poorly_drained_phosphorus_runoff_WGS84.tif",
    "p_drain":  "https://raw.githubusercontent.com/claire-middendorf/covercrop_tool/main/poorly_drained_phosphorus_drainflow_WGS84.tif",
}

###INTRO
col1, col2 = st.columns(2)

with col2:
    st.title("Cover Crop Tool")

with col1:
    st.image("science_assessment_logo.png", width=250) 

st.write("This is a draft tool for Component 2 of the Indiana Science Assessment!")

def text_box(text, color):
    st.markdown(f"""
        <div style="
            border-left: 5px solid {color};
            padding: 15px;
            border-radius: 5px;
            min-height: 120px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        ">
            {text}
        </div>
    """, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    text_box("STEP 1: Upload your input CSV", "#185AA3")

with col2:
    text_box("STEP 2: Click the 'Calculate Nutrient Loads and Reductions' button ", "#36B5C9")

with col3:
    text_box("STEP 3: View results and download the output CSV", "#4E9995")

st.divider()

####STEP 1
st.header("STEP 1")

st.write("Your CSV should have the following column names: Site, Latitude, Longitude, Area_ha")

sample_df = pd.DataFrame({
    "Site":      [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "Latitude":  [41.153094, 41.374763, 40.47838, 40.125029, 40.357634,
                  39.211989, 38.026666, 38.354327, 38.884623, 39.537343],
    "Longitude": [-86.943672, -85.491263, -86.738381, -86.073278, -84.927954,
                  -87.167986, -87.797371, -86.126304, -85.086253, -85.417474],
    "Area_ha":   [20, 59, 34, 102, 55, 26, 147, 77, 18, 61]
})

with st.expander("See Example"):
    st.dataframe(
    sample_df.head(5),
    use_container_width=True,
    column_config={
        "Latitude":  st.column_config.NumberColumn("Latitude",  format="%.6f"),
        "Longitude": st.column_config.NumberColumn("Longitude", format="%.6f"),
    }
)
#Get cover crop csv from user
uploaded_file = st.file_uploader(label = "Upload your CSV here" , type= "csv", 
                                 accept_multiple_files=False)

#Display table header and map
if uploaded_file is not None:
    user_data = pd.read_csv(uploaded_file)
    st.write("Upload Successful!")
    
    with st.expander("Header of Input CSV"):
        st.dataframe(
            user_data.head(5),
            use_container_width=True,
            column_config={
                "Latitude":  st.column_config.NumberColumn("Latitude",  format="%.6f"),
                "Longitude": st.column_config.NumberColumn("Longitude", format="%.6f"),
            } )
    
    with st.expander("Map of Input CSV (max 50 points)"):
        st.map(data = user_data.head(50), latitude="Latitude", longitude="Longitude", size=4)



###Helper Functions


def create_calc_df(user_input):
    calc_csv = user_input.copy()
    
    calc_csv = pd.concat([calc_csv, pd.DataFrame(columns= ["N Load Drainflow (kg/ha)",
                "N Load Runoff (kg/ha)","P Load Drainflow (kg/ha)","P Load Runoff (kg/ha)",
                "N Load Drainflow (kg)", "N Load Runoff (kg)","P Load Drainflow (kg)",
                "P Load Runoff (kg)", "N Drainflow Reduction (kg)", "N Runoff Reduction (kg)",
                "P Drainflow Reduction (kg)","P Runoff Reduction (kg)"])])
    
    return calc_csv

def sample_raster(filepath, lat, lon):
    vsicurl_path = "/vsicurl/" + filepath
    with rasterio.open(vsicurl_path) as src:
        row, col = rowcol(src.transform, lon, lat)
        value = src.read(1)[row, col]
        return float(value)

def nutrient_calcs(inputcsv):
    
    for index, row in inputcsv.iterrows():
        lat = row["Latitude"]
        lon = row["Longitude"]
        area = row["Area_ha"]
        
        n_runoff_load = sample_raster(RASTER_PATHS["n_runoff"], lat, lon)
        n_drain_load  = sample_raster(RASTER_PATHS["n_drain"],  lat, lon)
        p_runoff_load = sample_raster(RASTER_PATHS["p_runoff"], lat, lon)
        p_drain_load  = sample_raster(RASTER_PATHS["p_drain"],  lat, lon)
        
        #Loads (kg/ha) from rasters hosted in GitHub
        inputcsv.at[index, "N Load Drainflow (kg/ha)"] = round(n_drain_load, 2)
        inputcsv.at[index, "N Load Runoff (kg/ha)"] = round(n_runoff_load,2)
        inputcsv.at[index, "P Load Drainflow (kg/ha)"] = round(p_drain_load,2)
        inputcsv.at[index, "P Load Runoff (kg/ha)"] = round(p_runoff_load,2)
        
        #Get load of area 
        inputcsv.at[index, "N Load Drainflow (kg)"] = round(n_drain_load * area, 2)
        inputcsv.at[index, "N Load Runoff (kg)"] = round(n_runoff_load * area,2)
        inputcsv.at[index, "P Load Drainflow (kg)"] = round(p_drain_load * area, 2)
        inputcsv.at[index, "P Load Runoff (kg)"] = round(p_runoff_load * area, 2)
        
        #Reduction from Cover Crops 
        inputcsv.at[index, "N Drainflow Reduction (kg)"] = round(n_drain_load * area * 0.34, 2)
        inputcsv.at[index, "N Runoff Reduction (kg)"] = "Neutral"
        inputcsv.at[index, "P Drainflow Reduction (kg)"] = "Insufficient Data"
        inputcsv.at[index, "P Runoff Reduction (kg)"] = "Insufficient Data"
        
    # Define which columns to sum
    sum_cols = [
            "N Load Drainflow (kg)",
            "N Load Runoff (kg)",
            "P Load Drainflow (kg)",
            "P Load Runoff (kg)",
            "N Drainflow Reduction (kg)",
            "N Runoff Reduction (kg)",
            "P Drainflow Reduction (kg)",
            "P Runoff Reduction (kg)"
        ]
        
    # Build the summary row
    summary_row = {col: "" for col in inputcsv.columns}
    summary_row["Site"] = "TOTALS"
        
    for col in sum_cols:
        numeric_vals = pd.to_numeric(inputcsv[col], errors="coerce").dropna()
            
        if len(numeric_vals) == 0:
                # All entries were strings
                summary_row[col] = "N/A"
        else:
                # At least some numeric entries — sum those
                summary_row[col] = numeric_vals.sum()
        
    inputcsv = pd.concat([inputcsv, pd.DataFrame([summary_row])], ignore_index=True)
        
    return inputcsv

st.divider()

####STEP 2
st.header("STEP 2")

#Button to Initiate Calculations
if st.button("Calculate Nutrient Loads and Reductions", type = "primary"):
    if uploaded_file is None:
        st.warning("⚠️ Please upload a CSV file in Step 1 before calculating.")
    else:
        calc_df = create_calc_df(user_data)
        output_df = nutrient_calcs(calc_df)
        output_csv = output_df.to_csv(index = False).encode("utf-8")
        # everything indented here only runs when the button is clicked 
        st.write("Calculations Successful!")   
        with st.expander("Header of Result CSV"):
            st.dataframe(
            output_df.head(12),
            use_container_width=True,
            column_config={
                "Latitude":  st.column_config.NumberColumn("Latitude",  format="%.6f"),
                "Longitude": st.column_config.NumberColumn("Longitude", format="%.6f"),
            })
            
        st.divider()
        
        ####STEP 3
        #Show some pretty results
        st.header("STEP 3")
        
        st.download_button(
                label="Download Output CSV",
                data= output_csv,
                file_name= "covercrop_results.csv",
                mime="text/csv",
                icon=":material/download:",)
        
        totals = output_df.loc[output_df["Site"] == "TOTALS"]
        
        st.write("💧 Without covercrops")
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("N Load Drainflow", f"{totals['N Load Drainflow (kg)'].values[0]:,.0f} kg")
        col2.metric("N Load Runoff",    f"{totals['N Load Runoff (kg)'].values[0]:,.0f} kg")
        col3.metric("P Load Drainflow", f"{totals['P Load Drainflow (kg)'].values[0]:,.0f} kg")
        col4.metric("P Load Runoff",    f"{totals['P Load Runoff (kg)'].values[0]:,.0f} kg")
        
        st.write(" 🌱 With covercrops")
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("N Drainflow Reduction", f"{totals['N Drainflow Reduction (kg)'].values[0]:,.0f} kg")
        col2.metric("N Runoff Reduction",    f"{totals['N Runoff Reduction (kg)'].values[0]}")
        col3.metric("P Drainflow Reduction", f"{totals['P Drainflow Reduction (kg)'].values[0]}")
        col4.metric("P Runoff Reduction",    f"{totals['P Runoff Reduction (kg)'].values[0]}")
        
        #st.map(data = output_df.head(50), latitude="Latitude", longitude="Longitude", size=4)
            



