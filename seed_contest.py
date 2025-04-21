import os
import json
import re
import config

def extract_author(content):
    """Extracts the author from the text content."""
    match = re.search(r"^(Autor|Autora):\s*(.*)", content, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(2).strip()
    return "Unknown Author"

def extract_title_from_content(content):
    """Extracts the title from the text content."""
    match = re.search(r"^Título:\s*(.*)", content, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None

def seed_contest(examples_dir, contest_name):
    """Reads text files from the examples directory and extracts contest data."""
    contest_data = {
        "contest_name": contest_name,
        "submissions": []
    }

    if not os.path.isdir(examples_dir):
        print(f"Error: Directory '{examples_dir}' not found.")
        return None

    for filename in os.listdir(examples_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(examples_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                author = extract_author(content)
                # Use title from content if available, otherwise from filename
                title_from_content = extract_title_from_content(content)
                title_from_filename = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
                title = title_from_content if title_from_content else title_from_filename

                submission = {
                    "title": title,
                    "author": author,
                    "filename": filename,
                    # Optionally include the full text:
                    # "text": content 
                }
                contest_data["submissions"].append(submission)
                print(f"Processed: {filename} (Title: {title}, Author: {author})")

            except Exception as e:
                print(f"Error processing file {filename}: {e}")

    return contest_data

def save_data(data, output_file):
    """Saves the contest data to a JSON file."""
    if data:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"\nContest data successfully saved to {output_file}")
        except Exception as e:
            print(f"Error saving data to {output_file}: {e}")

def run_seeding():
    """Main function to run the contest seeding process."""
    print(f"Seeding contest '{config.CONTEST_NAME}'...")
    data = seed_contest(config.EXAMPLES_DIR, config.CONTEST_NAME)
    save_data(data, config.OUTPUT_FILE)

if __name__ == "__main__":
    run_seeding() 