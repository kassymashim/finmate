"""Generate PDF from presentation HTML - one page per slide."""
import asyncio
from playwright.async_api import async_playwright
import os

async def generate_pdf():
    html_path = os.path.join(os.path.dirname(__file__), "presentation.html")
    pdf_path = os.path.join(os.path.dirname(__file__), "FinMate_Presentation.pdf")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto(f"file:///{html_path.replace(os.sep, '/')}")
        await page.wait_for_timeout(1000)
        
        # Get total slides count
        total = await page.evaluate("document.querySelectorAll('.slide').length")
        print(f"Found {total} slides")
        
        # Make all slides visible for PDF
        await page.evaluate("""
            document.querySelectorAll('.slide').forEach(s => {
                s.style.display = 'flex';
                s.style.pageBreakAfter = 'always';
                s.style.height = '100vh';
                s.style.width = '100vw';
            });
            document.querySelector('.nav').style.display = 'none';
            document.querySelector('.progress').style.display = 'none';
            document.querySelector('.slide-num').style.display = 'none';
        """)
        
        await page.pdf(
            path=pdf_path,
            format="A4",
            landscape=True,
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        
        await browser.close()
        print(f"PDF saved to: {pdf_path}")

asyncio.run(generate_pdf())
