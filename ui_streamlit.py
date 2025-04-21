import streamlit as st
import yaml
from pathlib import Path
from main import main as process_files
import logging

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def save_config(config):
    with open("config.yaml", "w") as f:
        yaml.dump(config, f)

def main():
    st.title("AI File Organizer")
    
    # Load current config
    config = load_config()
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # Source directory
    source_dir = st.sidebar.text_input(
        "Source Directory",
        value=config["source_directory"]
    )
    
    # Destination directory
    dest_dir = st.sidebar.text_input(
        "Destination Directory",
        value=config["destination_directory"]
    )
    
    # Model selection
    model = st.sidebar.selectbox(
        "AI Model",
        ["distilbert-base-uncased", "bert-base-uncased", "roberta-base"],
        index=0 if config["ai_settings"]["model"] == "distilbert-base-uncased" else 1
    )
    
    # Device selection
    device = st.sidebar.selectbox(
        "Device",
        ["cpu", "cuda"],
        index=0 if config["ai_settings"]["device"] == "cpu" else 1
    )
    
    # Save configuration
    if st.sidebar.button("Save Configuration"):
        config["source_directory"] = source_dir
        config["destination_directory"] = dest_dir
        config["ai_settings"]["model"] = model
        config["ai_settings"]["device"] = device
        save_config(config)
        st.sidebar.success("Configuration saved!")
    
    # Main content
    st.header("File Processing")
    
    if st.button("Process Files"):
        with st.spinner("Processing files..."):
            try:
                process_files()
                st.success("Files processed successfully!")
            except Exception as e:
                st.error(f"Error processing files: {str(e)}")
    
    # Display logs
    st.header("Logs")
    log_file = Path("logs/file_organizer.log")
    if log_file.exists():
        with open(log_file, "r") as f:
            logs = f.read()
        st.text_area("Recent Logs", logs, height=300)
    else:
        st.info("No logs available yet.")

if __name__ == "__main__":
    main() 