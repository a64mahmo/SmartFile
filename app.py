import streamlit as st
import yaml
from pathlib import Path
import logging
from file_scanner import FileScanner
from content_extractor import ContentExtractor
from ai_categorizer import AICategorizer
from file_mover import FileMover
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom CSS to hide the hamburger menu
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def load_config():
    """Load configuration from YAML file."""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return {}

def save_operation_log(operation):
    """Save operation details to a JSON log file."""
    try:
        log_file = Path("logs/operations.json")
        log_file.parent.mkdir(exist_ok=True)
        
        operations = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                operations = json.load(f)
        
        operations.append(operation)
        
        with open(log_file, 'w') as f:
            json.dump(operations, f, indent=2)
        logger.info(f"Saved operation to log: {operation}")
    except Exception as e:
        logger.error(f"Error saving operation log: {str(e)}")

def main():
    st.title("AI File Organizer")
    
    # Load configuration
    config = load_config()
    logger.info("Loaded configuration")
    
    # Initialize components
    scanner = FileScanner(supported_extensions=config.get("supported_extensions", ['.pdf', '.docx', '.txt', '.md', '.pptx', '.dmg', '.xlsx']))
    extractor = ContentExtractor()
    
    # Extract AI settings
    ai_settings = config.get("ai_settings", {})
    model_name = ai_settings.get("model_name", "facebook/bart-large-mnli")
    device = ai_settings.get("device", "cpu")
    categorizer = AICategorizer(model_name=model_name, device=device)
    
    # Initialize FileMover with destination directory
    mover = FileMover(destination_dir=Path(config["destination_directory"]))
    
    # File upload section
    st.header("Upload Files")
    uploaded_files = st.file_uploader("Choose files to organize", accept_multiple_files=True)
    
    if uploaded_files:
        # Process files
        processed_files = set()
        for uploaded_file in uploaded_files:
            if uploaded_file.name in processed_files:
                continue
                
            try:
                logger.info(f"Processing file: {uploaded_file.name}")
                
                # Save uploaded file temporarily
                temp_path = Path("temp") / uploaded_file.name
                temp_path.parent.mkdir(exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Extract content
                content = extractor.extract_content(temp_path)
                if not content:
                    st.warning(f"No content extracted from {uploaded_file.name}")
                    logger.warning(f"No content extracted from {uploaded_file.name}")
                    continue
                
                # Analyze and categorize
                result = categorizer.analyze_and_categorize(content, temp_path)
                st.info(f"Suggested category for {uploaded_file.name}: {result['category']}")
                logger.info(f"Suggested category for {uploaded_file.name}: {result['category']}")
                
                # Move file
                destination = mover.move_file(
                    temp_path,
                    result["new_filename"],
                    result["category"]
                )
                if destination:
                    st.success(f"Moved {uploaded_file.name} to {destination}")
                    logger.info(f"Moved {uploaded_file.name} to {destination}")
                    processed_files.add(uploaded_file.name)
                    
                    # Save operation details
                    operation = {
                        'timestamp': datetime.now().isoformat(),
                        'source': str(temp_path),
                        'destination': str(destination),
                        'category': result['category'],
                        'new_name': result['new_filename'],
                        'confidence': result.get('confidence', 0.0)
                    }
                    save_operation_log(operation)
                else:
                    st.error(f"Failed to move {uploaded_file.name}")
                    logger.error(f"Failed to move {uploaded_file.name}")
                    
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                logger.error(f"Error processing {uploaded_file.name}: {str(e)}")
                continue
                
        st.success("File organization process completed")
        logger.info("File organization process completed")

if __name__ == "__main__":
    main() 