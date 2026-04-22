
import os
import glob
import asyncio
from playwright.async_api import async_playwright

async def render_svgs(svg_dir):
    svg_files = glob.glob(os.path.join(svg_dir, "*.svg"))
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for svg_file in svg_files:
            png_file = svg_file.replace(".svg", ".png")
            print(f"正在渲染: {os.path.basename(svg_file)} -> PNG")
            
            # 使用 html 包裹 svg
            with open(svg_file, 'r', encoding='utf-8') as f:
                svg_content = f.read()
                
            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ margin: 0; padding: 20px; background: white; }}
                </style>
            </head>
            <body>
                {svg_content}
            </body>
            </html>
            '''
            
            await page.set_content(html_content)
            
            # 找到 svg 元素并截图
            svg_element = await page.locator('svg').first
            if svg_element:
                await svg_element.screenshot(path=png_file, omit_background=True)
            else:
                await page.screenshot(path=png_file, full_page=True)
                
        await browser.close()

if __name__ == "__main__":
    svg_dir = r"E:\lawai\output\doc\diagrams	ables"
    asyncio.run(render_svgs(svg_dir))
