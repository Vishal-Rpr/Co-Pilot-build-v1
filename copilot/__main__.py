"""CLI interface for PM Co-pilot."""

import click
from .rag import ingest_references, retrieve
from .agent import generate_prd, generate_tickets


@click.group()
def cli():
    """PM Co-pilot: RAG-powered PRD generation with Linear, Jira, Confluence, and Excalidraw support."""
    pass


@cli.command()
def ingest():
    """Ingest reference PRDs and tickets into the vector store."""
    click.echo("Ingesting reference documents...")
    try:
        counts = ingest_references()
        for doc_type, count in counts.items():
            click.echo(f"  {doc_type}: {count} chunks")
        click.echo(f"Done. {sum(counts.values())} total chunks stored.")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("topic")
@click.option("--context", "-c", default="", help="Additional context for the PRD.")
@click.option("--no-rag", is_flag=True, help="Skip RAG retrieval, use generic template.")
@click.option("--output", "-o", default=None, help="Save PRD to file.")
def generate(topic: str, context: str, no_rag: bool, output: str):
    """Generate a PRD for a given topic."""
    click.echo(f"Generating PRD for: {topic}")

    retrieved = ""
    if not no_rag:
        click.echo("Retrieving style examples from your reference docs...")
        retrieved = retrieve(topic, doc_type="prd")
        if retrieved:
            click.echo("Found relevant style examples. Generating with your voice...")
        else:
            click.echo("No reference docs ingested yet. Using standard template.")

    prd = generate_prd(topic=topic, retrieved_chunks=retrieved, context=context)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(prd)
        click.echo(f"\nPRD saved to: {output}")
    else:
        click.echo("\n" + "=" * 60)
        click.echo(prd)
        click.echo("=" * 60)


@cli.command()
@click.argument("prd_file", type=click.Path(exists=True))
@click.option(
    "--target", "-t",
    type=click.Choice(["linear", "jira"], case_sensitive=False),
    default="linear",
    help="Target tracker: linear (default) or jira.",
)
def tickets(prd_file: str, target: str):
    """Break a PRD file into tickets for Linear or Jira."""
    with open(prd_file, "r", encoding="utf-8") as f:
        content = f.read()

    ticket_style = retrieve(content[:200], doc_type="ticket")
    if ticket_style:
        click.echo("Found reference tickets. Matching your ticket style...")

    click.echo(f"Generating tickets from: {prd_file} (target: {target})")
    result = generate_tickets(content, retrieved_chunks=ticket_style)
    click.echo("\n" + result)


@cli.command()
@click.argument("feature")
@click.option("--output", "-o", default=None, help="Save diagram to .excalidraw file.")
def diagram(feature: str, output: str):
    """Generate an Excalidraw diagram for a feature or workflow."""
    from .excalidraw import generate_diagram as gen_diag

    click.echo(f"Generating diagram for: {feature}")

    try:
        diagram_json = gen_diag(feature)
    except Exception as e:
        click.echo(f"Error generating diagram: {e}", err=True)
        raise SystemExit(1)

    if output:
        if not output.endswith(".excalidraw"):
            output += ".excalidraw"
        with open(output, "w", encoding="utf-8") as f:
            f.write(diagram_json)
        click.echo(f"Diagram saved to: {output}")
    else:
        click.echo("\n" + diagram_json)


@cli.command()
@click.argument("prd_file", type=click.Path(exists=True))
@click.option(
    "--to",
    type=click.Choice(["confluence"], case_sensitive=False),
    required=True,
    help="Target platform to publish to.",
)
@click.option("--space", "-s", required=True, help="Confluence space key.")
@click.option("--title", "-t", default=None, help="Page title (defaults to first heading in file).")
@click.option("--parent", "-p", default=None, help="Parent page ID for nesting.")
def publish(prd_file: str, to: str, space: str, title: str, parent: str):
    """Publish a PRD to Confluence."""
    from .confluence_client import create_page

    with open(prd_file, "r", encoding="utf-8") as f:
        content = f.read()

    if not title:
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break
        if not title:
            title = prd_file.replace(".md", "").replace("_", " ").title()

    click.echo(f"Publishing '{title}' to Confluence space {space}...")

    try:
        result = create_page(
            title=title,
            body_markdown=content,
            space_key=space,
            parent_id=parent,
        )
        click.echo(f"Published: {result['url']}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
