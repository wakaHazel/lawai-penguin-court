import os
import requests
import urllib.parse
import time

def generate_image_with_retry(prompt, output_path, retries=3):
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true"
    
    for attempt in range(retries):
        print(f"Attempt {attempt + 1} for {output_path}...")
        try:
            # Added custom User-Agent to avoid potential blocks and increased timeout
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Successfully saved image to {output_path}")
                return True
            elif response.status_code == 429:
                print("Rate limited, waiting 10 seconds...")
                time.sleep(10)
            else:
                print(f"❌ Failed to generate image, status code: {response.status_code}")
                time.sleep(5)
        except Exception as e:
            print(f"❌ Error generating image: {e}")
            time.sleep(5)
            
    print(f"Failed to generate {output_path} after {retries} attempts.")
    return False

def main():
    os.makedirs("E:/lawai/data/cg-library/cartoon-court", exist_ok=True)
    
    prompts = {
        "stage_debate.png": "A cute anthropomorphic penguin wearing a judge's robe sitting behind a high wooden judge's bench in a realistic modern Chinese courtroom. Below, two penguins in suits stand at the plaintiff and defendant wooden tables facing each other. Realistic modern courtroom interior with wooden panels and national emblem style decor on the wall (but no specific text). Vector illustration style, flat colors, serious legal atmosphere. Absolutely no text, no letters, no watermarks.",
        
        "stage_report_ready.png": "A cute anthropomorphic penguin in a suit holding a neat paper folder with a big green checkmark on it. The background is a clean, realistic modern meeting room with a whiteboard showing simple pie charts and bar graphs drawn with markers. Vector illustration style, flat colors, professional and bright. Absolutely no text, no letters, no words, no numbers, no watermarks anywhere."
    }
    
    base_dir = "E:/lawai/data/cg-library/cartoon-court"
    
    for filename, prompt in prompts.items():
        output_path = os.path.join(base_dir, filename)
        generate_image_with_retry(prompt, output_path)
        time.sleep(5)

if __name__ == "__main__":
    main()
