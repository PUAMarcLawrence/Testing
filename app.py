import streamlit as st
import graphviz as gv
import sqlite3
import pandas as pd  # For displaying the table

# Function to retrieve all table names in the database
def get_table_names(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    except sqlite3.Error as e:
        st.error(f"Database connection error: {e}")
        return []

# Function to load subjects from the selected table, including the "Title" column
def load_subjects_from_db(db_path, table_name):
    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as e:
        st.error(f"Database connection error: {e}")
        return {}

    cursor = conn.cursor()
    
    # Updated query to include Title
    query = f"""
    SELECT Year, Term, Code, Title, Prerequisites, Co_requisites 
    FROM {table_name};
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    subjects = {}
    
    for row in rows:
        year, term, subject_code, title, prerequisites, corequisites = row
        prerequisites = prerequisites.split(',') if prerequisites else []
        corequisites = corequisites.split(',') if corequisites else []

        semester_key = f"{year} - {term}"
        if semester_key not in subjects:
            subjects[semester_key] = {}
        
        subjects[semester_key][subject_code] = {
            "title": title,  # Store the title
            "prerequisites": [prereq.strip() for prereq in prerequisites],
            "corequisites": [coreq.strip() for coreq in corequisites]
        }
    
    conn.close()
    
    return subjects

# Function to build the subject graph with color-coded edges
def build_subject_graph(subjects):
    dot = gv.Digraph()
    dot.attr(splines='true')
    dot.attr(rankdir='LR', size='10,5', nodesep='0.1', ranksep='0.51', dpi='70')

    # Define color map for semesters (you can customize these colors)
    semester_color_map = {
        "1 - 2": "#ff0000",
        "1 - 3": "#00ff00",
        "1 - 4": "#ff00ff",

        "2 - 1": "#ffff00",
        "2 - 2": "#00ffff",
        "2 - 3": "#9900ff",
        "2 - 4": "#ff9900",

        "3 - 1": "#ff0099",
        "3 - 2": "#33cc33",
        "3 - 3": "#ff3300",
        "3 - 4": "black",

        "4 - 1": "#cc3300",
        "4 - 2": "#ffff00",
        "4 - 3": "#00ffff",
        "4 - 4": "black",
        # Add more semesters and colors as needed
    }

    for semester, semester_subjects in subjects.items():
        semester_color = semester_color_map.get(semester, "black")  # Default to black if no color is defined

        with dot.subgraph() as s:
            s.attr(rank='same')
            for subject, details in semester_subjects.items():
                s.node(subject, subject, shape='box', style='rounded,filled', fontsize='10', width='0.001', height='0.0001', fillcolor="white")

                # Add edges for prerequisites, using color coding based on the semester
                for prereq in details['prerequisites']:
                    dot.edge(f"{prereq}:e", f"{subject}:w", color=semester_color)  # Color-coded edge for prerequisites

                # Add edges for corequisites, using a dashed blue line and color-coding for other edges
                for coreq in details['corequisites']:
                    dot.edge(coreq, subject, style='dashed', dir='none', color='#0082c8',penwidth='3')  # Color-coded corequisites

    return dot



# Function to format subjects for legend, including Title and color coding
def format_subjects_for_legend(subjects):
    legend_data = []
    for semester, semester_subjects in subjects.items():
        for subject, details in semester_subjects.items():
            title = details['title']  # Add title to the legend data
            prerequisites = ', '.join(details['prerequisites']) if details['prerequisites'] else "None"
            corequisites = ', '.join(details['corequisites']) if details['corequisites'] else "None"
            legend_data.append([semester, subject, title, prerequisites, corequisites])
    
    # Create a DataFrame
    df = pd.DataFrame(legend_data, columns=["Semester", "Subject Code", "Title", "Prerequisites", "Co-requisites"])

    # Define color map for semesters
    color_map = {
        "1 - 1": "background-color: lightblue",
        "1 - 2": "background-color: lightgreen",
        "1 - 3": "background-color: lightblue",
        "1 - 4": "background-color: lightgreen",
        "2 - 1": "background-color: lightblue",
        "2 - 2": "background-color: lightgreen",
        "2 - 3": "background-color: lightblue",
        "2 - 4": "background-color: lightgreen",
        "3 - 1": "background-color: lightblue",
        "3 - 2": "background-color: lightgreen",
        "3 - 3": "background-color: lightblue",
        "3 - 4": "background-color: lightgreen",
        "4 - 1": "background-color: lightblue",
        "4 - 2": "background-color: lightgreen",
        "4 - 3": "background-color: lightblue",
        "4 - 4": "background-color: lightgreen",
    }

    # Function to apply the color coding
    def highlight_semester(row):
        return [color_map.get(row['Semester'], "") for _ in row]

    # Apply the style
    styled_df = df.style.apply(highlight_semester, axis=1)
    return styled_df

# Main app logic
db_path = 'ece.db'  # Change this to your database path
tables = get_table_names(db_path)

if tables:
    selected_table = st.selectbox("Select a curriculum:", tables,index=tables.index('ECE2021'))

    subjects = load_subjects_from_db(db_path, selected_table)

    if subjects:

        # Build and display the graph
        graph = build_subject_graph(subjects)
        st.graphviz_chart(graph)
        
        # Display the subjects table as a legend, including Title
        legend_df = format_subjects_for_legend(subjects)
        st.subheader(f"Subjects and Requirements from {selected_table}")
        st.table(legend_df)  # Display the table with title
        
else:
    st.error("No tables found in the database.")
