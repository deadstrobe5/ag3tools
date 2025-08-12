"""
Context7 MCP tool - Easy access to library documentation and code examples.

Context7 provides up-to-date, version-specific documentation and code examples
for various libraries and frameworks directly into your prompts.

Usage:
    from ag3tools.tools.smithery.repertoire import context7

    # Find React libraries
    libs = context7.find_library("react")

    # Get documentation
    docs = context7.get_docs("react", "hooks")

    # Or use direct shortcuts
    docs = context7.get_react_docs("useState useEffect")
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from ..core import get, call


SERVER_NAME = "@upstash/context7-mcp"
_server = None


@dataclass
class LibraryInfo:
    """Information about a library from Context7."""
    id: str
    title: str
    description: str
    snippets: int
    trust_score: float
    versions: Optional[List[str]] = None


def load():
    """
    Load the Context7 server and register its tools.

    Returns:
        The loaded server instance
    """
    global _server
    if _server is None:
        _server = get(SERVER_NAME)
    return _server


def find_library(name: str) -> List[LibraryInfo]:
    """
    Find libraries matching the given name.

    Args:
        name: Library name to search for (e.g., "react", "vue", "tensorflow")

    Returns:
        List of LibraryInfo objects for matching libraries
    """
    load()  # Ensure server is loaded

    result = call(SERVER_NAME, "resolve-library-id", libraryName=name)

    libraries = []
    if result and len(result) > 0:
        text = result[0].text if hasattr(result[0], 'text') else str(result[0])

        # Parse the text output
        lines = text.split('\n')
        current_lib = {}

        for i, line in enumerate(lines):
            line = line.strip()

            if line.startswith("- Title:"):
                if current_lib and 'id' in current_lib:
                    # Save previous library
                    libraries.append(LibraryInfo(
                        id=current_lib['id'],
                        title=current_lib.get('title', ''),
                        description=current_lib.get('description', ''),
                        snippets=int(current_lib.get('snippets', 0)),
                        trust_score=float(current_lib.get('trust_score', 0.0)),
                        versions=current_lib.get('versions')
                    ))
                current_lib = {'title': line.replace("- Title:", "").strip()}

            elif line.startswith("- Context7-compatible library ID:"):
                current_lib['id'] = line.replace("- Context7-compatible library ID:", "").strip()

            elif line.startswith("- Description:"):
                current_lib['description'] = line.replace("- Description:", "").strip()

            elif line.startswith("- Code Snippets:"):
                try:
                    current_lib['snippets'] = line.replace("- Code Snippets:", "").strip()
                except:
                    current_lib['snippets'] = 0

            elif line.startswith("- Trust Score:"):
                try:
                    current_lib['trust_score'] = line.replace("- Trust Score:", "").strip()
                except:
                    current_lib['trust_score'] = 0.0

            elif line.startswith("- Versions:"):
                versions_str = line.replace("- Versions:", "").strip()
                current_lib['versions'] = [v.strip() for v in versions_str.split(',')]

        # Don't forget the last library
        if current_lib and 'id' in current_lib:
            libraries.append(LibraryInfo(
                id=current_lib['id'],
                title=current_lib.get('title', ''),
                description=current_lib.get('description', ''),
                snippets=int(current_lib.get('snippets', 0)),
                trust_score=float(current_lib.get('trust_score', 0.0)),
                versions=current_lib.get('versions')
            ))

    # Sort by trust score
    libraries.sort(key=lambda x: x.trust_score, reverse=True)

    return libraries


def get_docs(library: str, topic: str = "", tokens: int = 2000) -> str:
    """
    Get documentation for a specific library.

    Args:
        library: Library name or Context7 ID (e.g., "react" or "/facebook/react")
        topic: Specific topic to focus on (e.g., "hooks", "routing")
        tokens: Maximum tokens to retrieve (default: 2000)

    Returns:
        Documentation content as string
    """
    load()  # Ensure server is loaded

    # If it's not a Context7 ID, resolve it first
    if not library.startswith("/"):
        libs = find_library(library)
        if libs:
            # Use the highest trust score library
            library = libs[0].id
        else:
            raise ValueError(f"No library found for '{library}'")

    # Get the documentation
    result = call(
        SERVER_NAME,
        "get-library-docs",
        context7CompatibleLibraryID=library,
        topic=topic,
        tokens=tokens
    )

    # Extract text content
    if result:
        if hasattr(result, '__iter__') and len(result) > 0:
            return result[0].text if hasattr(result[0], 'text') else str(result[0])
        else:
            return str(result)

    return ""


# Convenience functions for popular libraries

def get_react_docs(topic: str = "", tokens: int = 2000) -> str:
    """Get React documentation."""
    return get_docs("/reactjs/react.dev", topic, tokens)


def get_nextjs_docs(topic: str = "", tokens: int = 2000) -> str:
    """Get Next.js documentation."""
    return get_docs("/vercel/next.js", topic, tokens)


def get_vue_docs(topic: str = "", tokens: int = 2000) -> str:
    """Get Vue.js documentation."""
    return get_docs("/vuejs/vue", topic, tokens)


def get_python_docs(topic: str = "", tokens: int = 2000) -> str:
    """Get Python documentation."""
    libs = find_library("python")
    if libs:
        return get_docs(libs[0].id, topic, tokens)
    return ""


def get_tensorflow_docs(topic: str = "", tokens: int = 2000) -> str:
    """Get TensorFlow documentation."""
    libs = find_library("tensorflow")
    if libs:
        return get_docs(libs[0].id, topic, tokens)
    return ""


def get_pytorch_docs(topic: str = "", tokens: int = 2000) -> str:
    """Get PyTorch documentation."""
    libs = find_library("pytorch")
    if libs:
        return get_docs(libs[0].id, topic, tokens)
    return ""


# Export main functions
__all__ = [
    'load',
    'find_library',
    'get_docs',
    'get_react_docs',
    'get_nextjs_docs',
    'get_vue_docs',
    'get_python_docs',
    'get_tensorflow_docs',
    'get_pytorch_docs',
    'LibraryInfo'
]
