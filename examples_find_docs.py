from ag3tools.core.types import FindDocsInput
from ag3tools.tools.docs.find_docs import find_docs


def main():
    result = find_docs(FindDocsInput(technology="langgraph"))
    print(result)


if __name__ == "__main__":
    main()


