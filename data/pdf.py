import os
import json
import time
import feedparser
from pathlib import Path
from datetime import datetime
import requests

# === Configuration ===
FIELD_QUERIES = {
    'computer_science': ['machine learning', 'algorithms', 'computer vision', 'natural language processing', 'databases'],
    'mathematics': ['algebra', 'calculus', 'topology', 'number theory', 'statistics'],
    'physics': ['quantum mechanics', 'thermodynamics', 'electromagnetism', 'astrophysics', 'particle physics'],
    'chemistry': ['organic chemistry', 'inorganic chemistry', 'analytical chemistry', 'physical chemistry', 'biochemistry'],
    'biology': ['genetics', 'molecular biology', 'ecology', 'neuroscience', 'microbiology'],
    'engineering': ['civil engineering', 'mechanical engineering', 'electrical engineering', 'chemical engineering', 'aerospace engineering']
}

ARXIV_API_URL = "http://export.arxiv.org/api/query"
TARGET_PAPERS_PER_FIELD = 1500
PAGE_SIZE = 100
MAX_PAGES_PER_SUBFIELD = 8
DELAY_BETWEEN_REQUESTS = 7
BASE_PATH = "C:/Users/nshej/aisearch/data/metadata"

# === Utilities ===
def load_existing_ids(field):
    seen = set()
    folder_path = Path(BASE_PATH) / field
    if folder_path.exists():
        for json_file in folder_path.glob("*.json"): #glob working is basially pattern matching of file it take the **.file type use for retrieving the data
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                    for paper in batch_data:
                        if paper.get('arxiv_id'):
                            seen.add(paper['arxiv_id'])
            except Exception as e:
                print(f"  ⚠️ Could not load {json_file.name}: {e}")
    return seen

def extract_arxiv_metadata(feed, seen_ids, field):
    metadata_list = []
    for entry in feed.entries:
        arxiv_id = entry.get("id")
        if not arxiv_id or arxiv_id in seen_ids:
            continue
        seen_ids.add(arxiv_id)

        metadata = {
            'title': entry.get("title"),
            'abstract': entry.get("summary"),
            'authors': [author.name for author in entry.authors],
            'publication_date': entry.get("published"),
            'arxiv_id': arxiv_id,
            'download_url': entry.get("link"),
            'field_of_study': field,
            'document_type': "preprint",
            'citation_count': None, #to improve the quality of the data u can use the citation right now it is none but u can use the .get("citation_Count")
            'source_repository': "arXiv"
        }
        metadata_list.append(metadata)
    return metadata_list

def save_batch(field, papers, batch_num):
    folder_path = Path(BASE_PATH) / field
    folder_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = folder_path / f"batch_{batch_num:02d}_{timestamp}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    return file_path

def get_field_stats(field):
    folder_path = Path(BASE_PATH) / field
    if not folder_path.exists():
        return 0, 0
    total_papers = 0
    files = list(folder_path.glob("*.json"))
    for json_file in files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
                total_papers += len(batch_data)
        except:
            pass
    return len(files), total_papers

# === Main Execution ===
print("=" * 70)
print("arXiv Metadata Collection - Multi-Query Strategy")
print("=" * 70)
print(f"Target: {TARGET_PAPERS_PER_FIELD} papers per field")
print(f"Page Size: {PAGE_SIZE} papers per request")
print(f"Strategy: Multiple specific subfield queries to reduce duplicates")
print("=" * 70)

seen_ids = {field: load_existing_ids(field) for field in FIELD_QUERIES.keys()}

print("\n📊 Current Progress:")
for field in FIELD_QUERIES.keys():
    batches, papers = get_field_stats(field)
    print(f"  {field.replace('_', ' ').title()}: {papers}/{TARGET_PAPERS_PER_FIELD} papers ({batches} files)")

try:
    for field, subfield_queries in FIELD_QUERIES.items():
        field_name = field.replace('_', ' ').title()
        current_batches, current_papers = get_field_stats(field)

        if current_papers >= TARGET_PAPERS_PER_FIELD:
            print(f"\n✅ {field_name}: Target reached ({current_papers} papers)")
            continue

        print(f"\n{'='*70}")
        print(f"📚 Collecting for: {field_name}")
        print(f"   Current: {current_papers}/{TARGET_PAPERS_PER_FIELD} papers")
        print(f"{'='*70}")

        batch_num = current_batches + 1

        for subfield in subfield_queries:
            if current_papers >= TARGET_PAPERS_PER_FIELD:
                break

            print(f"\n  🔎 Searching: '{subfield}'")

            for page in range(1, MAX_PAGES_PER_SUBFIELD + 1):
                if current_papers >= TARGET_PAPERS_PER_FIELD:
                    break

                print(f"    Page {page}/{MAX_PAGES_PER_SUBFIELD}...", end=" ")

                start = (page - 1) * PAGE_SIZE
                params = {
                    "search_query": f"all:{subfield}",
                    "start": start,
                    "max_results": PAGE_SIZE
                }

                try:
                    response = requests.get(ARXIV_API_URL, params=params, timeout=30)
                    feed = feedparser.parse(response.text)
                except Exception as e:
                    print(f"❌ Request failed: {e}")
                    break

                if not feed.entries:
                    print("❌ No results")
                    break

                metadata_batch = extract_arxiv_metadata(feed, seen_ids[field], field)
                total_returned = len(feed.entries)
                unique_count = len(metadata_batch)

                if unique_count == 0:
                    print(f"⚠️ All {total_returned} duplicates")
                    if total_returned < PAGE_SIZE * 0.5:
                        break
                else:
                    file_path = save_batch(field, metadata_batch, batch_num)
                    current_papers += unique_count
                    batch_num += 1
                    print(f"✅ Saved {unique_count}/{total_returned} papers (Total: {current_papers})")

                time.sleep(DELAY_BETWEEN_REQUESTS)

        final_batches, final_papers = get_field_stats(field)
        print(f"\n  📊 {field_name} Summary: {final_papers}/{TARGET_PAPERS_PER_FIELD} papers in {final_batches} files")

    print("\n" + "="*70)
    print("✨ Collection Complete!")
    print("="*70)
    print("\n📊 Final Statistics:")
    for field in FIELD_QUERIES.keys():
        batches, papers = get_field_stats(field)
        progress = (papers / TARGET_PAPERS_PER_FIELD) * 100
        print(f"  {field.replace('_', ' ').title():.<30} {papers:>3}/{TARGET_PAPERS_PER_FIELD} ({progress:.1f}%)")

except KeyboardInterrupt:
    print("\n\n⏸️ Process interrupted by user.")
    print("Progress has been saved. Run again to resume.")
except Exception as e:
    print(f"\n\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
