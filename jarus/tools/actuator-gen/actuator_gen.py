#!/usr/bin/env python3
"""
Actuator Generator - Genetic Encoding for The Blade of Truth Capabilities
========================================================================

Generates new actuator services with full compliance to the organism's
architectural principles: immune response (policy gating), circulatory
routing (ledger integration), and nervous system integration (registry).

Usage:
    python actuator_gen.py --name legal_compliance --sector legal --port 5011 \
        --capabilities '["contract_review", "policy_check"]'
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("ERROR: jinja2 is required. Install with: pip install jinja2")
    sys.exit(1)


def generate_actuator(name: str, sector: str, port: int, capabilities: list):
    """Generate a new actuator service from templates."""

    # Validate inputs
    if not name.replace('_', '').isalnum():
        print(f"ERROR: Actuator name must be alphanumeric with underscores: {name}")
        sys.exit(1)

    # Determine paths
    script_dir = Path(__file__).parent
    template_dir = script_dir / "templates"

    # Output to services directory (relative to sovereign-system root)
    project_root = script_dir.parent.parent
    output_dir = project_root / "services" / name

    if output_dir.exists():
        print(f"WARNING: Directory {output_dir} already exists. Overwriting...")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True
    )

    # Template files to render
    templates = [
        ('main.py.j2', 'main.py'),
        ('Dockerfile.j2', 'Dockerfile'),
        ('__init__.py.j2', '__init__.py'),
        ('.env.example.j2', '.env.example'),
    ]

    print(f"\n{'='*60}")
    print(f"ACTUATOR GENERATOR - The Blade of Truth")
    print(f"{'='*60}")
    print(f"Creating actuator: {name}")
    print(f"Sector: {sector}")
    print(f"Port: {port}")
    print(f"Capabilities: {capabilities}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")

    # Render each template
    for template_name, output_name in templates:
        try:
            template = env.get_template(template_name)
            output_path = output_dir / output_name

            content = template.render(
                actuator_name=name,
                sector=sector,
                port=port,
                capabilities=capabilities
            )

            with open(output_path, 'w') as f:
                f.write(content)

            print(f"  [+] Created {output_path}")

        except Exception as e:
            print(f"  [!] Error creating {output_name}: {e}")

    print(f"\n{'='*60}")
    print("GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"\nNext steps:")
    print(f"  1. Review generated files in: {output_dir}")
    print(f"  2. Implement mission logic in main.py")
    print(f"  3. Run: python compose_helper.py --name {name} --port {port}")
    print(f"  4. Add the generated block to docker-compose.runtime.yml")
    print(f"  5. Deploy: docker-compose -f docker-compose.runtime.yml up --build -d")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate a new actuator service for the The Blade of Truth"
    )
    parser.add_argument(
        '--name',
        required=True,
        help='Snake_case name for the actuator (e.g., legal_compliance)'
    )
    parser.add_argument(
        '--sector',
        required=True,
        help='Sector this actuator serves (e.g., legal, finance, operations)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5007,
        help='Port for the actuator service (default: 5007)'
    )
    parser.add_argument(
        '--capabilities',
        type=str,
        default='[]',
        help='JSON array of capability strings (e.g., \'["review", "analyze"]\')'
    )

    args = parser.parse_args()

    # Parse capabilities
    try:
        capabilities = json.loads(args.capabilities)
        if not isinstance(capabilities, list):
            raise ValueError("Capabilities must be a JSON array")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON for capabilities: {e}")
        sys.exit(1)

    generate_actuator(
        name=args.name,
        sector=args.sector,
        port=args.port,
        capabilities=capabilities
    )


if __name__ == '__main__':
    main()

