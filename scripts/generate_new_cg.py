import os
import requests
import urllib.request
import json
import time

def generate_image(prompt, output_path):
    print(f"Generating image for prompt: {prompt}")
    
    # Since we don't have a configured GEMINI_API_KEY in the env directly visible to this python script without dotenv,
    # and relying on external API might fail if keys are missing or quota exceeded in this sandboxed environment,
    # I will simulate the image generation by using a placeholder image service (like Unsplash Source or Placehold.co)
    # OR we can try to call the project's own gemini client if it's fully configured.
    # Given the constraint of ensuring this works 100% for the user's document, 
    # I will use a reliable high-quality placeholder service to generate beautiful gradient/abstract images 
    # that look like polished UI mockups, but since the user specifically asked for "Penguin in a real modern court", 
    # I will use Pollinations.ai which can generate AI images via a simple GET request without API keys!
    
    encoded_prompt = urllib.parse.quote(prompt)
    # Pollinations.ai allows free text-to-image generation via URL
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Successfully saved image to {output_path}")
        else:
            print(f"❌ Failed to generate image, status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error generating image: {e}")

def main():
    # Ensure directory exists
    os.makedirs("E:/lawai/data/cg-library/cartoon-court", exist_ok=True)
    
    # 提示词已完全去掉科幻、全息等元素，回归现代真实的法庭和办公室场景。
    # 强调：No text, no letters, no watermark.
    
    prompts = {
        "stage_prepare.png": "A cute anthropomorphic penguin wearing a black suit, sitting at a realistic modern wooden office desk. On the desk are neat stacks of paper legal documents and a standard computer monitor. The background is a bright, realistic modern law firm office. Vector illustration style, flat colors, professional and serious atmosphere. Absolutely no text, no letters, no watermarks, no words anywhere in the image.",
        
        "stage_debate.png": "A cute anthropomorphic penguin wearing a judge's robe sitting behind a high wooden judge's bench in a realistic modern Chinese courtroom. Below, two penguins in suits stand at the plaintiff and defendant wooden tables facing each other. Realistic modern courtroom interior with wooden panels and national emblem style decor on the wall (but no specific text). Vector illustration style, flat colors, serious legal atmosphere. Absolutely no text, no letters, no watermarks.",
        
        "stage_report_ready.png": "A cute anthropomorphic penguin in a suit holding a neat paper folder with a big green checkmark on it. The background is a clean, realistic modern meeting room with a whiteboard showing simple pie charts and bar graphs drawn with markers. Vector illustration style, flat colors, professional and bright. Absolutely no text, no letters, no words, no numbers, no watermarks anywhere."
    }
    
    base_dir = "E:/lawai/data/cg-library/cartoon-court"
    
    for filename, prompt in prompts.items():
        output_path = os.path.join(base_dir, filename)
        generate_image(prompt, output_path)
        time.sleep(2) # be nice to the free API

if __name__ == "__main__":
    main()
