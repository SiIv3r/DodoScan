
import time
import random
import requests
from bs4 import BeautifulSoup
import typer
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
app = typer.Typer()
console = Console()
ascii_art = """
·▄▄▄▄        ·▄▄▄▄        .▄▄ ·  ▄▄·  ▄▄▄·  ▐ ▄ 
██▪ ██ ▪     ██▪ ██ ▪     ▐█ ▀. ▐█ ▌▪▐█ ▀█ •█▌▐█
▐█· ▐█▌ ▄█▀▄ ▐█· ▐█▌ ▄█▀▄ ▄▀▀▀█▄██ ▄▄▄█▀▀█ ▐█▐▐▌
██. ██ ▐█▌.▐▌██. ██ ▐█▌.▐▌▐█▄▪▐█▐███▌▐█ ▪▐▌██▐█▌
▀▀▀▀▀•  ▀█▄▀▪▀▀▀▀▀•  ▀█▄▀▪ ▀▀▀▀ ·▀▀▀  ▀  ▀ ▀▀ █▪         
"""
DORKS = {
    "sensitive_files": 'inurl:"/backup/" | inurl:"/config/" | inurl:"/private/" | inurl:"/secrets/" | inurl:"/hidden/"',
    "login_pages": 'inurl:"/login/" | inurl:"/admin/" | inurl:"/user/" | inurl:"/portal/" | inurl:"/signin/"',
    "database_files": 'ext:sql | ext:db | ext:mdb | ext:accdb | ext:sqlite | ext:sqlite3',
    "env_files": 'ext:env | intext:"DB_PASSWORD" | intext:"APP_KEY" | intext:"SECRET_KEY"',
    "log_files": 'ext:log | inurl:"logs/" | inurl:"error_log" | inurl:"/debug.log"',
    "config_files": 'inurl:"/config/" -github | ext:conf | ext:ini | ext:cfg | ext:cnf',
    "php_errors": 'ext:php intitle:"Warning" | intitle:"Error" | "Fatal error"',
    "exposed_docs": 'filetype:doc | filetype:xls | filetype:docx | filetype:xlsx | filetype:ppt | filetype:pptx',
    "public_git_repos": 'inurl:".git" | inurl:".git/config" | inurl:".gitignore"',
    "directory_listing": 'intitle:"index of" | intitle:"parent directory"',
    "password_exposure": 'intext:"password" filetype:txt | intext:"login" filetype:csv | intext:"passwd"',
    "open_cameras": 'intitle:"webcamXP 5" | intitle:"Live View / - AXIS" | inurl:"view/view.shtml"',
    "ftp_servers": 'intitle:"index of" inurl:ftp | inurl:"ftp://"',
    "phpinfo_exposure": 'ext:php intitle:"phpinfo()"',
    "emails_exposure": 'intext:"@gmail.com" | intext:"@yahoo.com" | intext:"@hotmail.com" | intext:"@outlook.com"',
    "database_dumps": 'ext:sql | ext:db | ext:mdb | ext:backup | inurl:"dump.sql"',
    "backup_files": 'inurl:"/backup" | inurl:"/backups" | filetype:zip | filetype:tar | filetype:gz | filetype:bak | filetype:old',
    "exposed_api_keys": 'intext:"API_KEY" | intext:"api_secret" | intext:"access_token" | intext:"AWS_SECRET_ACCESS_KEY"',
    "s3_buckets": 'site:s3.amazonaws.com | site:storage.googleapis.com | site:drive.google.com',
    "error_logs": 'filetype:log "Apache" | "Nginx" | "error.log" | "mysql_error.log"',
    "admin_panels": 'inurl:"admin" | inurl:"administrator" | intitle:"Admin Login" | inurl:"wp-admin"',
    "exposed_private_keys": 'ext:key | ext:pem | ext:ppk | intext:"BEGIN RSA PRIVATE KEY"',
    "Jenkins_dashboard": 'intitle:"Dashboard [Jenkins]"',
    "Elasticsearch_exposure": 'intitle:"Elasticsearch" AND inurl:"_cat"',
    "Kibana_exposure": 'intitle:"Kibana" AND inurl:"app/kibana"',
    "Grafana_exposure": 'intitle:"Grafana" AND inurl:"/d/"',
    "GitLab_instances": 'intitle:"Sign in · GitLab"',
    "Confluence_exposure": 'intitle:"Confluence" AND inurl:"/pages/viewpage.action"',
    "JIRA_exposure": 'intitle:"JIRA" AND inurl:"/secure/Dashboard.jspa"',
    "RDP_login": 'intitle:"Remote Desktop Web Connection"',
    "VPN_login": 'intitle:"GlobalProtect Portal" | inurl:"/vpn/login"',
    "API_documentation": 'intitle:"Swagger UI" | inurl:"/swagger-ui.html"',
    "open_directories": 'intitle:"index of /" AND intext:"Last modified"',
    "Docker_registries": 'inurl:"v2/_catalog" | intitle:"Docker Registry"',
    "Kubernetes_dashboards": 'inurl:"/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/"'
}

def welcome_screen():
    console.print(f"\n[bold cyan]{ascii_art}[/bold cyan]")
    console.print("[green]This tool searches for sensitive files and admin pages on a specific domain. [/green]\n")
    console.print("[green]May make mistakes. Please space out searches to avoid getting blocked. [/green]\n")
    console.print("[cyan]For BTC donations : bc1qje465lpcs06ccmywj4fer76zhpz8rgav905jsg [/cyan]\n")

def get_user_input():
    domain = typer.prompt(" Enter the target domain (ex: example.com)")

    engine = typer.prompt(" Choose search engine (google, bing, duckduckgo) [RECOMMENDED: duckduckgo]")
    stealth = typer.confirm(" Enable stealth mode? (adds delays between requests) [RECOMMENDED]")

    return domain, engine, stealth

def search_engine(domain, dork, engine):
    query = f"site:{domain} {dork}"
    if engine == "google":
        url = f"https://www.google.com/search?q={query}"
    elif engine == "bing":
        url = f"https://www.bing.com/search?q={query}"
    elif engine == "duckduckgo":
        url = f"https://duckduckgo.com/html/?q={query}"
    else:
        console.print(f"[red] Error: Search engine '{engine}' not supported.[/red]")
        return []
    
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    if engine == "google":
        for item in soup.find_all("div", class_="tF2Cxc"):
            title = item.find("h3").text
            link = item.find("a")["href"]
            results.append({"title": title, "url": link})
    elif engine == "bing":
        for item in soup.find_all("li", class_="b_algo"):
            title = item.find("h2").text
            link = item.find("a")["href"]
            results.append({"title": title, "url": link})
    elif engine == "duckduckgo":
        for item in soup.find_all("div", class_="result__body"):
            title = item.find("h2").text
            link = item.find("a")["href"]
            results.append({"title": title, "url": link})
    
    return results

@app.command()
def run():
    welcome_screen()
    domain, engine, stealth = get_user_input()
    console.print("[cyan] Research in progress...[/cyan]")
    found_count = 0
    with Progress(
        TextColumn(" [cyan]Progress:[/cyan]"),
        BarColumn(),
        TimeElapsedColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        console=console
        
    ) as progress:
        task = progress.add_task("[green] Analysis of results...[/green]", total=len(DORKS))
        for dork_name, dork_query in DORKS.items():
            results = search_engine(domain, dork_query, engine)
            progress.update(task, advance=1)
            if stealth:
                time.sleep(random.uniform(1, 3))
            
            if results:

                found_count += 1
                console.print(f"[bold green]✔ {dork_name} find:[/bold green]")
                for result in results:
                    console.print(f"  {result['title']} - [blue]{result['url']}[/blue]")
            else:
                console.print(f"[bold red] {dork_name} not find.[/bold red]")
    console.print(f"\n[bold cyan] Out of {len(DORKS)} dorks analyzed, {found_count} gave results.[/bold cyan]")    

if __name__ == "__main__":
    run()
