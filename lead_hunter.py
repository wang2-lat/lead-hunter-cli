import typer
import praw
import requests
import csv
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = typer.Typer(help="🎯 Lead Hunter CLI - Find your customers on Reddit/HN/ProductHunt")

# Reddit setup
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT", "lead-hunter-cli/1.0")
)

def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    """从文本中提取联系方式"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    twitter_pattern = r'(?:twitter\.com/|@)([A-Za-z0-9_]{1,15})'
    linkedin_pattern = r'linkedin\.com/in/([A-Za-z0-9-]+)'
    
    email = re.search(email_pattern, text)
    twitter = re.search(twitter_pattern, text)
    linkedin = re.search(linkedin_pattern, text)
    
    return {
        "email": email.group(0) if email else None,
        "twitter": f"@{twitter.group(1)}" if twitter else None,
        "linkedin": f"linkedin.com/in/{linkedin.group(1)}" if linkedin else None
    }

def search_reddit(keyword: str, limit: int = 50) -> List[Dict]:
    """搜索 Reddit 相关帖子"""
    leads = []
    try:
        for submission in reddit.subreddit("all").search(keyword, limit=limit, sort="relevance"):
            # 提取作者信息
            author_name = str(submission.author) if submission.author else "deleted"
            if author_name == "deleted":
                continue
                
            # 获取帖子内容
            content = f"{submission.title}\n{submission.selftext}"
            contacts = extract_contact_info(content)
            
            # 检查评论中的联系方式
            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list()[:5]:
                if str(comment.author) == author_name:
                    comment_contacts = extract_contact_info(comment.body)
                    for key, value in comment_contacts.items():
                        if value and not contacts[key]:
                            contacts[key] = value
            
            leads.append({
                "platform": "Reddit",
                "author": author_name,
                "title": submission.title,
                "url": f"https://reddit.com{submission.permalink}",
                "content": submission.selftext[:200],
                "score": submission.score,
                **contacts
            })
    except Exception as e:
        typer.echo(f"❌ Reddit 搜索错误: {str(e)}", err=True)
    
    return leads

def search_hackernews(keyword: str, limit: int = 50) -> List[Dict]:
    """搜索 HackerNews 相关帖子"""
    leads = []
    try:
        # 使用 Algolia HN Search API
        url = f"https://hn.algolia.com/api/v1/search?query={keyword}&tags=story&hitsPerPage={limit}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        for hit in data.get("hits", []):
            author = hit.get("author", "")
            title = hit.get("title", "")
            url = hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID')}")
            
            # HN 不直接提供联系方式，需要访问用户页面
            contacts = {"email": None, "twitter": None, "linkedin": None}
            
            leads.append({
                "platform": "HackerNews",
                "author": author,
                "title": title,
                "url": url,
                "content": hit.get("story_text", "")[:200],
                "score": hit.get("points", 0),
                **contacts
            })
    except Exception as e:
        typer.echo(f"❌ HackerNews 搜索错误: {str(e)}", err=True)
    
    return leads

def search_producthunt(keyword: str, limit: int = 30) -> List[Dict]:
    """搜索 ProductHunt（简化版，使用公开页面）"""
    leads = []
    try:
        # ProductHunt 需要 API token，这里使用简化的 web scraping
        url = f"https://www.producthunt.com/search?q={keyword}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 注意：实际抓取需要根据 PH 的 HTML 结构调整
        typer.echo("⚠️  ProductHunt 需要 API token，当前为演示模式", err=True)
        
    except Exception as e:
        typer.echo(f"❌ ProductHunt 搜索错误: {str(e)}", err=True)
    
    return leads

def generate_email_template(lead: Dict) -> str:
    """生成个性化邮件模板"""
    template = f"""Subject: Re: {lead['title'][:50]}

Hi {lead['author']},

I came across your post on {lead['platform']} about "{lead['title']}" and found it really interesting.

{lead['content'][:100]}...

I thought you might be interested in [YOUR PRODUCT/SERVICE] because [SPECIFIC REASON BASED ON THEIR POST].

Would you be open to a quick chat about this?

Best regards,
[YOUR NAME]

---
P.S. Found via: {lead['url']}
"""
    return template

@app.command()
def search(
    keyword: str = typer.Argument(..., help="搜索关键词"),
    platforms: str = typer.Option("reddit,hn", help="平台列表，逗号分隔 (reddit,hn,ph)"),
    limit: int = typer.Option(30, help="每个平台的结果数量"),
    output: str = typer.Option("leads.csv", help="输出 CSV 文件名")
):
    """🔍 搜索潜在客户"""
    typer.echo(f"🎯 开始搜索关键词: {keyword}")
    
    all_leads = []
    platform_list = [p.strip().lower() for p in platforms.split(",")]
    
    if "reddit" in platform_list:
        typer.echo("📱 搜索 Reddit...")
        all_leads.extend(search_reddit(keyword, limit))
    
    if "hn" in platform_list:
        typer.echo("🔶 搜索 HackerNews...")
        all_leads.extend(search_hackernews(keyword, limit))
    
    if "ph" in platform_list:
        typer.echo("🚀 搜索 ProductHunt...")
        all_leads.extend(search_producthunt(keyword, limit))
    
    # 导出 CSV
    if all_leads:
        with open(output, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["platform", "author", "title", "url", "content", "score", "email", "twitter", "linkedin", "email_template"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for lead in all_leads:
                lead["email_template"] = generate_email_template(lead).replace("\n", " | ")
                writer.writerow(lead)
        
        typer.echo(f"✅ 找到 {len(all_leads)} 个潜在客户，已保存到 {output}")
        
        # 统计有联系方式的数量
        with_contact = sum(1 for l in all_leads if l.get("email") or l.get("twitter") or l.get("linkedin"))
        typer.echo(f"📧 其中 {with_contact} 个有联系方式")
    else:
        typer.echo("❌ 未找到相关结果", err=True)

@app.command()
def config():
    """⚙️  配置 API credentials"""
    typer.echo("请在 .env 文件中配置以下信息：")
    typer.echo("\n1. Reddit API (必需):")
    typer.echo("   - 访问 https://www.reddit.com/prefs/apps")
    typer.echo("   - 创建一个 'script' 类型的应用")
    typer.echo("   - 复制 client_id 和 client_secret 到 .env")
    typer.echo("\n2. OpenAI API (可选，用于高级邮件生成):")
    typer.echo("   - 访问 https://platform.openai.com/api-keys")
    typer.echo("   - 创建 API key 并添加到 .env")
    typer.echo("\n参考 .env.example 文件")

if __name__ == "__main__":
    app()