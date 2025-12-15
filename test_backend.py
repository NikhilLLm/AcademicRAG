"""Simple test script for backend endpoints."""
import requests
import json
from qdrant_client import QdrantClient
from datetime import datetime
import os

BASE_URL = "http://localhost:8000"
FIELDS = ["biology", "chemistry", "computer_science", "engineering", "mathematics", "physics"]
#check for available collections in qdrant
def collection_check():#there is no endpoint for this yet so check using qdrant

    """Check available collections in Qdrant."""
    client = QdrantClient(host="localhost", port=6333)

    existing = client.get_collections().collections
    existing_names = [c.name for c in existing]

    for field in FIELDS:
        if field.lower() in existing_names:
            print(f"✅ Collection '{field.lower()}' exists.")
        else:
            print(f"❌ Collection '{field.lower()}' does NOT exist. Collection field exists: {existing_names}")


def test_text_search():
    """Test the text search endpoint."""
    print("\n=== Testing Text Search ===")
    try:
        response = requests.post(
            f"{BASE_URL}/search_text",
            data={"query": "graph neural networks"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_image_upload():
    """Test the image upload endpoint."""
    print("\n=== Testing Image Upload ===")
    try:
        image_path = "C:/Users/nshej/aisearch/largepreview.png"
        with open(image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/upload_image", files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except FileNotFoundError:
        print("Error: Image file not found")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_pdf_upload():
    """Test the PDF upload endpoint."""
    print("\n=== Testing PDF Upload ===")
    try:
        pdf_path = "C:/Users/nshej/aisearch/ML_Challenge_202.pdf"
        with open(pdf_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/upload_pdf", files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except FileNotFoundError:
        print("Error: PDF file not found")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def get_notes(vector_index:str,collection_name:str):
    """Test the get short notes endpoint."""
    print("\n=== Testing Get Short Notes ===")
    try:
        response = requests.post(
            f"{BASE_URL}/get_short_notes",
            data={"vector_index": vector_index,"collection_name":collection_name}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        
        # Print notes with better formatting
        if "short_notes" in result:
            notes = result["short_notes"]
            metadata = result.get("metadata", {})
           
            print("\n📝 GENERATED NOTES:")
            print("-" * 60)
            print(notes[:200] + "..." if len(notes) > 200 else notes)
            print("-" * 60)
            
            # Save to test.md file
            with open("test.md", "a", encoding="utf-8") as f:
                f.write(f"\n\n# {metadata.get('title', 'Unknown Paper')}\n")
                f.write(f"**Field:** {collection_name}\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Authors:** {metadata.get('authors', 'N/A')}\n")
                f.write(f"**URL:** {metadata.get('download_url', 'N/A')}\n\n")
                f.write("## Notes\n")
                f.write(notes)
                f.write("\n\n" + "="*60)
            
            print(f"\n💾 Notes saved to: test.md")
        
        if "metadata" in result:
            print("\n📋 PAPER METADATA:")
            print(f"  Title: {result['metadata'].get('title', 'N/A')}")
            print(f"  Authors: {result['metadata'].get('authors', 'N/A')}")
        
        if "error" in result:
            print(f"⚠️ Error: {result['error']}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False
def test_server_health():
    """Check if server is running."""
    print("\n=== Testing Server Health ===")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Start it with: python -m backend.main")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("Backend API Test Script")
    print("=" * 50)
    #Check Collection First
    
    # Test server health first

    if not test_server_health():
        print("\nServer is not running. Please start it first:")
        print("  conda activate eye-env")
        print("  python -m backend.main")
        exit(1)
    
    # Run tests
    results = {
        # "Text Search": test_text_search(),
        # "Image Upload": test_image_upload(),
        # "PDF Upload": test_pdf_upload(),
        "get Short Notes": get_notes("f7ce21fb-97e2-57c8-b061-40133facb1fa","computer_science"),
    }
    
    # Summary
    # print("\n" + "=" * 50)
    # print("Test Results Summary:")
    # for test_name, passed in results.items():
    #     status = "✅ PASSED" if passed else "❌ FAILED"
    #     print(f"  {test_name}: {status}")
    
    # passed_count = sum(results.values())
    # print(f"\nTotal: {passed_count}/{len(results)} tests passed")
