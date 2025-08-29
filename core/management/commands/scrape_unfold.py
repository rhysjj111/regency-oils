import os
import time
from urllib.parse import urljoin, urlparse
import requests

from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup
import html2text

from playwright.sync_api import sync_playwright, TimeoutError

class Command(BaseCommand):
    help = 'Scrapes the Unfold documentation using a browser that scrolls.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Unfold documentation scrape (Browser Method)..."))

        sitemap_url = "https://unfoldadmin.com/sitemap.xml"
        output_dir = "unfold_docs_markdown"

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            self.stdout.write(f"Created output directory: {output_dir}")

        try:
            # Step 1: Get all URLs from sitemap.xml
            self.stdout.write(f"Fetching sitemap from {sitemap_url}")
            response = requests.get(sitemap_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml-xml')
            
            urls_to_scrape = []
            for loc in soup.find_all('loc'):
                url = loc.get_text()
                if "/docs/" in url:
                    urls_to_scrape.append(url)
            
            self.stdout.write(f"Found {len(urls_to_scrape)} documentation pages in the sitemap.")

            # Step 2: Scrape each page using Playwright
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()

                for i, url in enumerate(urls_to_scrape):
                    self.stdout.write(f"Scraping ({i+1}/{len(urls_to_scrape)}): {url}")
                    page.goto(url, wait_until="networkidle")
                    
                    try:
                        accept_button = page.get_by_role("button", name="Accept all")
                        accept_button.click(timeout=2000)
                    except TimeoutError:
                        pass

                    content_area_locator = page.locator('div.prose')
                    
                    pre_locators = content_area_locator.locator('pre')
                    count = pre_locators.count()

                    for i in range(count):
                        pre = pre_locators.nth(i)
                        
                        # --- THIS IS THE CRUCIAL FIX ---
                        # Scroll the element into view to trigger lazy-loading
                        pre.scroll_into_view_if_needed()
                        
                        code_tag = pre.locator('code')
                        
                        lang_class = (code_tag.get_attribute('class', timeout=2000)) or "language-text"
                        lang = lang_class.replace('language-', '').split(' ')[0] or 'text'
                        
                        code_text = pre.inner_text()
                        
                        markdown_code_block = f"\n```{lang}\n{code_text.strip()}\n```\n"

                        pre.evaluate('(element, newContent) => { element.outerHTML = newContent; }', markdown_code_block)
                    
                    html_content = page.content()
                    soup = BeautifulSoup(html_content, 'lxml')
                    content_area = soup.find('div', class_='prose')
                    
                    if content_area:
                        for img_tag in content_area.find_all('img'):
                            if img_tag.get('src'):
                                img_tag['src'] = urljoin(url, img_tag['src'])

                        h = html2text.HTML2Text()
                        h.body_width = 0
                        markdown = h.handle(str(content_area))
                        
                        path = urlparse(url).path.strip('/')
                        filename = path.replace('/', '_') + '.md'
                        if not filename.endswith('.md'):
                           filename = "index.md"
                        filepath = os.path.join(output_dir, filename)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(markdown)
                    else:
                        self.stdout.write(self.style.WARNING(f"  -> No content found for {url}"))
                    
                    time.sleep(0.5)

                browser.close()
                self.stdout.write(self.style.SUCCESS("\nScraping complete!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nAn error occurred: {e}"))