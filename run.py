"""
FinMate - Quick Launch Script
Generates sample data and starts the application.
"""

import subprocess
import sys
import os

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    print("=" * 50)
    print("  FinMate - Personal Finance Assistant")
    print("=" * 50)

    print("\n[1/3] Generating synthetic transaction data...")
    from backend.utils.generate_synthetic_data import save_data
    save_data()

    print("\n[2/3] Building knowledge base (RAG)...")
    from backend.rag.knowledge_rag import build_knowledge_base
    build_knowledge_base()

    print("\n[3/3] Launching Streamlit app...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "frontend/app.py",
        "--server.port=8501",
        "--browser.gatherUsageStats=false",
    ])


if __name__ == "__main__":
    main()
