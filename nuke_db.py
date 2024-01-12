from rich import print
from config.db import users_collection, content_collection

print("[yellow]-------------------------------------------------------------[/yellow]")
print("[red][b]WARNING: Collection Purge In Effect![/b][/red]")
users_collection.drop()
content_collection.drop()
print("[green]Nuke Complete.[/green]")
print("[yellow]-------------------------------------------------------------[/yellow]")
