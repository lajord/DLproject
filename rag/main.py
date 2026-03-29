import sys
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'data_traitement', '.env'))

from pipeline import ask


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py \"your question here\"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    print(f"\nQuestion: {question}\n")

    result = ask(question, verbose=True)

    print(f"\nAnswer:\n{result['answer']}\n")
    print("Sources:")
    for s in result["sources"]:
        label = s["source"]
        if s.get("section"):
            label += f" > {s['section']}"
        print(f"  [{s['score']:.3f}] {label}")


if __name__ == "__main__":
    main()
