import gzip
import sys

def restore_doctype(input_file, output_file):
    print(f"Restoring DOCTYPE to {input_file}...")
    with gzip.open(input_file, 'rb') as f_in:
        content = f_in.read().decode('utf-8')
    
    # Check if header already exists
    if '<!DOCTYPE transitSchedule SYSTEM' in content:
        print("DOCTYPE already exists.")
        return
    
    # Find the position of <transitSchedule>
    pos = content.find('<transitSchedule')
    if pos == -1:
        print("Could not find <transitSchedule> tag.")
        return
    
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE transitSchedule SYSTEM "http://www.matsim.org/files/dtd/transitSchedule_v2.dtd">\n\n'
    new_content = header + content[pos:]
    
    with gzip.open(output_file, 'wb') as f_out:
        f_out.write(new_content.encode('utf-8'))
    print("Done.")

if __name__ == "__main__":
    restore_doctype(sys.argv[1], sys.argv[2])
