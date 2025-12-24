import yaml
import os

def extract_front_matter(file_path):
    """Extract only the YAML front matter from a markdown file."""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    
    print(f"  Total lines: {len(lines)}")
    print(f"  First line: {repr(lines[0])}")
    print(f"  First line stripped: {repr(lines[0].strip())}")
    
    # Check if first line is ---
    if not lines or lines[0].strip() != '---':
        print(f"  First line check failed")
        return None
    
    print(f"  First line check passed, looking for closing ---")
    
    # Find closing ---
    yaml_lines = []
    for i in range(1, len(lines)):
        print(f"  Line {i}: {repr(lines[i][:50])}")
        if lines[i].strip() == '---':
            print(f"  Found closing --- at line {i}")
            # Found closing delimiter, parse the YAML
            yaml_content = ''.join(yaml_lines)
            print(f"  YAML content length: {len(yaml_content)}")
            print(f"  YAML preview: {yaml_content[:200]}")
            try:
                result = yaml.safe_load(yaml_content)
                print(f"  Successfully parsed: {result}")
                return result
            except yaml.YAMLError as e:
                print(f"  ✗ YAML Parse Error: {e}")
                return None
        yaml_lines.append(lines[i])
    
    print(f"  Never found closing ---")
    return None

if __name__ == "__main__":
    base_path = '/Users/krishnakorade/Developer/osp/agent-tools/skills'
    
    for d in os.listdir(base_path):
        if d.startswith('.'):  # Skip hidden files
            continue
            
        skill_path = os.path.join(base_path, d)
        file_path = os.path.join(skill_path, 'SKILLS.md')
        
        if os.path.isfile(file_path):
            print(f"\n{d}:")
            
            data = extract_front_matter(file_path)
            
            if data:
                print(f"  ✓ SUCCESS!")
            else:
                print(f"  ✗ FAILED")