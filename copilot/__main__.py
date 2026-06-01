"""CLI interface for PM Co-pilot."""

import click
from .rag import ingest_references, retrieve
from .agent import generate_prd, generate_tickets


@click.group()
def cli():
    """PM Co-pilot: RAG-powered PRD generation and Linear ticket creation."""
    pass


@cli.command()
def ingest():
    """Ingest reference PRDs from reference_docs/ into the vector store."""
    click.echo("Ingesting reference documents...")
    try:
        count = ingest_references()
        click.echo(f"Done. {count} chunks stored from your reference PRDs.")
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
        retrieved = retrieve(topic)
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
def tickets(prd_file: str):
    """Break a PRD file into Linear tickets."""
    with open(prd_file, "r", encoding="utf-8") as f:
        content = f.read()

    click.echo(f"Generating tickets from: {prd_file}")
    result = generate_tickets(content)
    click.echo("\n" + result)


if __name__ == "__main__":
    cli()
