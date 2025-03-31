import os
import re
import streamlit as st
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class SqlDocumentationManager:
    """Class responsible for managing SQL documentation.
    
    This class encapsulates the functionality to extract, process, and display
    SQL script documentation, including metadata and formatted content.
    """
    
    def __init__(self, sql_dir: Optional[str] = None):
        """Initialize the SQL documentation manager.
        
        Args:
            sql_dir: Directory containing SQL files (optional)
        """
        self.sql_dir = sql_dir
        self.sql_files: List[str] = []
        if sql_dir:
            self.load_sql_files()
    
    def load_sql_files(self) -> List[str]:
        """Load all SQL files from the specified directory, sorted alphabetically.
        
        Returns:
            List of complete paths to SQL files
        """
        if not self.sql_dir or not os.path.exists(self.sql_dir):
            return []
            
        self.sql_files = []
        for file in os.listdir(self.sql_dir):
            if file.endswith('.sql'):
                self.sql_files.append(os.path.join(self.sql_dir, file))
        
        self.sql_files = sorted(self.sql_files)
        return self.sql_files
    
    def extract_metadata(self, markdown_content: str) -> Dict[str, str]:
        """Extract metadata from markdown content.
        
        Args:
            markdown_content: Markdown content from SQL comments
            
        Returns:
            Dictionary containing metadata fields
        """
        metadata = {
            'title': 'Unknown',
            'author': 'Unknown',
            'created': 'Unknown',
            'modified': 'Unknown',
            'purpose': ''
        }
        
        # Extract title
        title_match = re.search(r'#\s+SQL\s+SCRIPT:\s+(.+?)\s*$', markdown_content, re.MULTILINE)
        if title_match:
            metadata['title'] = title_match.group(1)
        
        # Extract author
        author_match = re.search(r'\*\*Author:\*\*\s+(.+?)\s*$', markdown_content, re.MULTILINE)
        if author_match:
            metadata['author'] = author_match.group(1)
        
        # Extract created date
        created_match = re.search(r'\*\*Created:\*\*\s+(.+?)\s*$', markdown_content, re.MULTILINE)
        if created_match:
            metadata['created'] = created_match.group(1)
        
        # Extract modified date
        modified_match = re.search(r'\*\*Last Modified:\*\*\s+(.+?)\s*$', markdown_content, re.MULTILINE)
        if modified_match:
            metadata['modified'] = modified_match.group(1)
        
        # Extract purpose
        purpose_match = re.search(r'##\s+Purpose\s*(.+?)(?=##|$)', markdown_content, re.DOTALL)
        if purpose_match:
            metadata['purpose'] = purpose_match.group(1).strip()
        
        return metadata
    
    def extract_sql_and_comments(self, file_path: str) -> Tuple[str, str]:
        """Extract SQL code and comments from a SQL file.
        
        Args:
            file_path: Path to the SQL file
            
        Returns:
            Tuple containing (sql_code, markdown_content)
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            return f"Erro ao ler arquivo: {str(e)}", ""
        
        # Extract lines starting with -- for markdown, but ignore lines starting with -- | or -- |
        lines = content.split('\n')
        markdown_lines = []
        for line in lines:
            # Ignore comments that start with -- | or -- | which are meant to be excluded from markdown
            line_stripped = line.strip()
            if line_stripped.startswith('--') and not line_stripped.startswith('-- |') and not line_stripped.startswith('-- |'):
                # Remove the -- prefix and one space if present
                clean_line = re.sub(r'^--\s?', '', line)
                markdown_lines.append(clean_line)
        
        # Join the markdown lines back together
        markdown_content = '\n'.join(markdown_lines)
        
        # Return both the original SQL and the extracted markdown
        return content, markdown_content
    
    def clean_markdown_content(self, markdown_content: str) -> str:
        """Clean markdown content for formatted display.
        
        Args:
            markdown_content: Original markdown content
            
        Returns:
            Cleaned markdown content for display
        """
        clean_markdown = markdown_content
        # Remove the metadata section to avoid duplication since we display it separately
        clean_markdown = re.sub(
            r'^#\s+SQL\s+SCRIPT.*?\*\*Last Modified:\*\*.*?$', 
            '', 
            clean_markdown, 
            flags=re.DOTALL | re.MULTILINE
        )
        return clean_markdown.strip()
    
    def display_documentation(self, sql_dir: Optional[str] = None) -> None:
        """Display SQL documentation with code on the left and markdown on the right.
        
        Args:
            sql_dir: Optional directory containing SQL files (overrides the class directory)
        """
        if sql_dir:
            self.sql_dir = sql_dir
            self.load_sql_files()
        
        if not self.sql_files:
            st.warning("No SQL files found in the directory.")
            return
        
        # Create a selectbox for user to choose which SQL file to view
        file_options = [os.path.basename(f) for f in self.sql_files]
        selected_file = st.selectbox("Select SQL File", file_options)
        
        # Get the selected file's full path
        selected_path = os.path.join(self.sql_dir, selected_file)
        
        # Extract SQL and markdown content
        sql_code, markdown_content = self.extract_sql_and_comments(selected_path)
        
        # Extract metadata
        metadata = self.extract_metadata(markdown_content)
        
        # Display script metadata in expander
        with st.expander("Script Metadata", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Title:** {metadata['title']}")
                st.markdown(f"**Author:** {metadata['author']}")
            with col2:
                st.markdown(f"**Created:** {metadata['created']}")
                st.markdown(f"**Last Modified:** {metadata['modified']}")
            
            st.markdown("**Purpose:**")
            st.markdown(f"_{metadata['purpose']}_")
        
        # Display main content in two columns
        code_col, doc_col = st.columns(2)
        
        with code_col:
            st.subheader("SQL Code")
            
            # Display the SQL code with line numbers
            st.code(sql_code, language="sql")
        
        with doc_col:
            st.subheader("Documentation")
            
            # Parse markdown to improve formatting
            clean_markdown = self.clean_markdown_content(markdown_content)
            
            st.markdown(clean_markdown)


# Compatibility function for existing code
def display_sql_documentation(sql_dir: str) -> None:
    """Compatibility function that uses the SqlDocumentationManager class.
    
    Args:
        sql_dir: Directory containing SQL files
    """
    doc_manager = SqlDocumentationManager()
    doc_manager.display_documentation(sql_dir)
